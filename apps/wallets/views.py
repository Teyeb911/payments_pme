from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdmin, IsCommerçant
from core.utils import success_response
from .models import Wallet
from .serializers import ChargerWalletSerializer, WalletSerializer


class MyWalletView(generics.RetrieveAPIView):
    """GET — solde et infos du wallet du commerçant connecté."""
    serializer_class   = WalletSerializer
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get_object(self):
        return get_object_or_404(Wallet, commercant=self.request.user)


class ChargerWalletView(APIView):
    """POST — charger le wallet depuis un compte externe."""
    permission_classes = [IsAuthenticated, IsCommerçant]

    @db_transaction.atomic
    def post(self, request):
        serializer = ChargerWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        montant       = serializer.validated_data['montant']
        id_compte_ext = serializer.validated_data['id_compte_ext']

        from apps.comptes.models import CompteExterne
        from apps.transactions.models import Transaction

        compte = get_object_or_404(
            CompteExterne,
            id=id_compte_ext,
            commercant=request.user,
            is_actif=True,
        )
        wallet = get_object_or_404(Wallet, commercant=request.user, is_active=True)
        wallet.crediter(montant)

        Transaction.objects.create(
            wallet_expediteur = wallet,
            wallet_recepteur  = wallet,
            commercant        = request.user,
            compte_externe    = compte,
            montant           = montant,
            frais             = 0,
            type              = Transaction.Type.CHARGEMENT,
            statut            = Transaction.Statut.SUCCESS,
            description       = f'Chargement depuis {compte.nom_banque}',
        )

        return Response(
            success_response(
                data=WalletSerializer(wallet).data,
                message=f'Wallet chargé de {montant} {wallet.currency}.',
            ),
            status=status.HTTP_200_OK,
        )


# ── Admin ─────────────────────────────────────────────
class AllWalletsView(generics.ListAPIView):
    """GET (admin) — liste de tous les wallets."""
    queryset           = Wallet.objects.select_related('commercant').order_by('-created_at')
    serializer_class   = WalletSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    search_fields      = ['commercant__email', 'commercant__nom']
