from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.transactions.models import Transaction
from apps.wallets.models import Wallet
from core.permissions import IsCommerçant, IsOwnerOrAdmin
from core.utils import success_response
from .models import CompteExterne, TransactionExterne
from .serializers import (
    CompteExterneSerializer,
    CompteExterneCreateSerializer,
    PaiementEntrantSerializer,
    TransactionExterneSerializer,
    TransactionExterneCreateSerializer,
)


class TransactionExternePagination(PageNumberPagination):
    """Pagination à 10 éléments par page pour les transactions externes."""
    page_size             = 10
    page_size_query_param = 'page_size'
    max_page_size         = 100

    def get_paginated_response(self, data):
        return Response({
            'count':    self.page.paginator.count,
            'pages':    self.page.paginator.num_pages,
            'next':     self.get_next_link(),
            'previous': self.get_previous_link(),
            'results':  data,
        })


class CompteListCreateView(generics.ListCreateAPIView):
    """
    GET  — liste des comptes externes du commerçant connecté.
    POST — lier un nouveau compte externe.
    """
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CompteExterneCreateSerializer
        return CompteExterneSerializer

    def get_queryset(self):
        return CompteExterne.objects.filter(
            commercant=self.request.user
        ).order_by('-created_at')


class CompteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — détail d'un compte.
    PATCH  — modifier (ex: api_token).
    DELETE — délier le compte.
    """
    serializer_class   = CompteExterneSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return CompteExterne.objects.filter(commercant=self.request.user)

    def destroy(self, request, *args, **kwargs):
        compte = self.get_object()
        compte.is_actif = False
        compte.save(update_fields=['is_actif'])
        return Response(
            success_response(message='Compte délié avec succès.'),
            status=status.HTTP_200_OK,
        )


class PaiementsEntrantsView(APIView):
    """
    GET — récupère les paiements entrants depuis le compte externe.
    (Simulation — à remplacer par l'API bancaire réelle)
    """
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get(self, request, pk):
        compte = get_object_or_404(
            CompteExterne,
            id=pk,
            commercant=request.user,
            is_actif=True,
        )

        # ── Simulation paiements entrants ──
        # En production : appel API bancaire avec compte.api_token
        paiements = [
            {
                'reference':  'PAY-001',
                'montant':    15000.00,
                'date':       '2025-03-01T10:00:00Z',
                'expediteur': 'Client A',
                'description': 'Paiement commande #101',
            },
            {
                'reference':  'PAY-002',
                'montant':    8500.00,
                'date':       '2025-03-02T14:30:00Z',
                'expediteur': 'Client B',
                'description': 'Règlement facture #55',
            },
        ]

        serializer = PaiementEntrantSerializer(paiements, many=True)
        return Response(success_response(data={
            'compte': compte.nom_banque,
            'paiements': serializer.data,
        }))


class TransactionExterneListCreateView(generics.ListCreateAPIView):
    """
    GET  — liste paginée des transactions d'un compte externe.
           Filtres : ?type=credit/debit, ?statut=completed/pending/failed
    POST — ajouter manuellement une transaction externe.
    """
    permission_classes = [IsAuthenticated, IsCommerçant]
    pagination_class   = TransactionExternePagination

    def get_queryset(self):
        compte_id = self.kwargs.get('pk')
        compte = get_object_or_404(
            CompteExterne,
            id=compte_id,
            commercant=self.request.user,
        )
        qs = TransactionExterne.objects.filter(
            compte_externe=compte
        ).select_related('compte_externe')

        # Filtres optionnels
        type_tx = self.request.query_params.get('type')
        if type_tx:
            qs = qs.filter(type_transaction=type_tx)

        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)

        return qs.order_by('-date')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TransactionExterneCreateSerializer
        return TransactionExterneSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            compte_id = self.kwargs.get('pk')
            compte = get_object_or_404(
                CompteExterne,
                id=compte_id,
                commercant=self.request.user,
            )
            context['compte_externe'] = compte
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            success_response(
                data=TransactionExterneSerializer(serializer.instance).data,
                message='Transaction ajoutée avec succès.',
            ),
            status=status.HTTP_201_CREATED,
        )


class ToutesTransactionsExternesView(generics.ListAPIView):
    """
    GET — toutes les transactions de tous les comptes externes de l'utilisateur.
    Triées par date décroissante, paginées (10 par page).
    """
    serializer_class   = TransactionExterneSerializer
    permission_classes = [IsAuthenticated, IsCommerçant]
    pagination_class   = TransactionExternePagination

    def get_queryset(self):
        return TransactionExterne.objects.filter(
            compte_externe__commercant=self.request.user
        ).select_related('compte_externe').order_by('-date')


class DashboardExternesView(APIView):
    """
    GET — vue consolidée du portefeuille numérique incluant les comptes externes.
    """
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get(self, request):
        now = timezone.now()
        comptes = CompteExterne.objects.filter(
            commercant=request.user,
            is_actif=True,
        ).prefetch_related('transactions_externes')

        comptes_data = []
        patrimoine_total = 0
        total_revenus_mois = 0
        total_depenses_mois = 0

        for compte in comptes:
            txs = compte.transactions_externes.all()

            # Agrégations séparées : mois courant + toutes périodes (pour le patrimoine)
            stats = txs.aggregate(
                credits_mois=Sum(
                    'montant',
                    filter=Q(
                        type_transaction=TransactionExterne.TypeTransaction.CREDIT,
                        date__year=now.year,
                        date__month=now.month,
                    )
                ),
                debits_mois=Sum(
                    'montant',
                    filter=Q(
                        type_transaction=TransactionExterne.TypeTransaction.DEBIT,
                        date__year=now.year,
                        date__month=now.month,
                    )
                ),
                credits_total=Sum(
                    'montant',
                    filter=Q(type_transaction=TransactionExterne.TypeTransaction.CREDIT)
                ),
                debits_total=Sum(
                    'montant',
                    filter=Q(type_transaction=TransactionExterne.TypeTransaction.DEBIT)
                ),
            )

            credits_mois  = stats['credits_mois']  or 0
            debits_mois   = stats['debits_mois']   or 0
            credits_total = stats['credits_total'] or 0
            debits_total  = stats['debits_total']  or 0

            patrimoine_total    += credits_total - debits_total
            total_revenus_mois  += credits_mois
            total_depenses_mois += debits_mois

            dernieres = txs.order_by('-date')[:5]

            comptes_data.append({
                'id': compte.id,
                'banque': compte.nom_banque,
                'numero': compte.numero_compte,
                'total_credits_mois': float(credits_mois),
                'total_debits_mois':  float(debits_mois),
                'nb_transactions': txs.count(),
                'dernieres_transactions': TransactionExterneSerializer(dernieres, many=True).data,
            })

        # ── Wallet TrackPay ──────────────────────────────
        wallet = Wallet.objects.filter(commercant=request.user).first()
        if wallet:
            total_envoye = Transaction.objects.filter(
                wallet_expediteur=wallet,
                statut=Transaction.Statut.SUCCESS,
                created_at__year=now.year,
                created_at__month=now.month,
            ).aggregate(total=Sum('montant'))['total'] or 0

            total_recu = Transaction.objects.filter(
                wallet_recepteur=wallet,
                statut=Transaction.Statut.SUCCESS,
                created_at__year=now.year,
                created_at__month=now.month,
            ).aggregate(total=Sum('montant'))['total'] or 0

            wallet_data = {
                'solde':             float(wallet.balance),
                'total_envoye_mois': float(total_envoye),
                'total_recu_mois':   float(total_recu),
            }
            patrimoine_total += wallet.balance
        else:
            wallet_data = {'solde': 0, 'total_envoye_mois': 0, 'total_recu_mois': 0}

        data = {
            'wallet_trackpay':        wallet_data,
            'comptes_externes':       comptes_data,
            'patrimoine_total_estime': float(patrimoine_total),
            'total_revenus_mois':     float(total_revenus_mois),
            'total_depenses_mois':    float(total_depenses_mois),
        }

        return Response(success_response(data=data))
