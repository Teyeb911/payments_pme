from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdmin, IsCommerçant
from core.utils import success_response
from apps.wallets.models import Wallet
from .filters import TransactionFilter
from .models import Transaction
from .serializers import (
    DashboardSerializer,
    TransactionSerializer,
    TransfertInterneSerializer,
)
from .services import TransfertService


# ─────────────────────────────────────────────────────
#  Historique — commerçant connecté
# ─────────────────────────────────────────────────────
class HistoriqueView(generics.ListAPIView):
    """GET — toutes les transactions du commerçant (envoyées + reçues)."""
    serializer_class   = TransactionSerializer
    permission_classes = [IsAuthenticated, IsCommerçant]
    filterset_class    = TransactionFilter
    search_fields      = ['reference', 'description']
    ordering_fields    = ['created_at', 'montant']
    ordering           = ['-created_at']

    def get_queryset(self):
        wallet = get_object_or_404(Wallet, commercant=self.request.user)
        return Transaction.objects.filter(
            Q(wallet_expediteur=wallet) | Q(wallet_recepteur=wallet)
        ).select_related(
            'commercant',
            'wallet_expediteur__commercant',
            'wallet_recepteur__commercant',
        )


# ─────────────────────────────────────────────────────
#  Détail transaction
# ─────────────────────────────────────────────────────
class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class   = TransactionSerializer
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get_queryset(self):
        wallet = get_object_or_404(Wallet, commercant=self.request.user)
        return Transaction.objects.filter(
            Q(wallet_expediteur=wallet) | Q(wallet_recepteur=wallet)
        )


# ─────────────────────────────────────────────────────
#  Transfert interne (GRATUIT)
# ─────────────────────────────────────────────────────
class TransfertInterneView(APIView):
    """POST — transfert wallet → wallet (frais = 0)."""
    permission_classes = [IsAuthenticated, IsCommerçant]

    def post(self, request):
        serializer = TransfertInterneSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            transaction = TransfertService.executer(
                expediteur  = request.user,
                recepteur   = serializer.get_recepteur(),
                montant     = serializer.validated_data['montant'],
                description = serializer.validated_data.get('description', ''),
            )
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            success_response(
                data=TransactionSerializer(transaction).data,
                message='Transfert effectué avec succès. Frais : 0 DZD',
            ),
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────
#  Annuler une transaction
# ─────────────────────────────────────────────────────
class AnnulerTransactionView(APIView):
    permission_classes = [IsAuthenticated, IsCommerçant]

    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, id=pk)
        try:
            transaction = TransfertService.annuler(transaction, request.user)
        except (ValueError, PermissionError) as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(success_response(
            data=TransactionSerializer(transaction).data,
            message='Transaction annulée.',
        ))


# ─────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────
class DashboardView(APIView):
    """GET — résumé financier complet du commerçant."""
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get(self, request):
        wallet = get_object_or_404(Wallet, commercant=request.user)

        qs_emises = Transaction.objects.filter(
            wallet_expediteur=wallet,
            statut=Transaction.Statut.SUCCESS,
        )
        qs_recues = Transaction.objects.filter(
            wallet_recepteur=wallet,
            statut=Transaction.Statut.SUCCESS,
        )
        dernieres = Transaction.objects.filter(
            Q(wallet_expediteur=wallet) | Q(wallet_recepteur=wallet)
        ).order_by('-created_at')[:10]

        data = {
            'wallet_balance':          wallet.balance,
            'total_envoye':            qs_emises.aggregate(t=Sum('montant'))['t'] or 0,
            'total_recu':              qs_recues.aggregate(t=Sum('montant'))['t'] or 0,
            'nb_transactions':         qs_emises.count() + qs_recues.count(),
            'dernières_transactions':  dernieres,
        }

        return Response(success_response(data=DashboardSerializer(data).data))


# ─────────────────────────────────────────────────────
#  Admin — toutes les transactions
# ─────────────────────────────────────────────────────
class AllTransactionsView(generics.ListAPIView):
    queryset           = Transaction.objects.select_related(
        'commercant',
        'wallet_expediteur__commercant',
        'wallet_recepteur__commercant',
    ).order_by('-created_at')
    serializer_class   = TransactionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_class    = TransactionFilter
    search_fields      = ['reference', 'commercant__email']
    ordering_fields    = ['created_at', 'montant', 'statut']
