from decimal import Decimal
from django.db import transaction as db_transaction
from rest_framework.exceptions import ValidationError
from apps.wallets.models import Wallet
from .models import Transaction


class TransfertService:
    """
    Toute la logique métier du transfert interne.
    Isolée dans un service pour rester indépendante des vues.
    """

    @staticmethod
    @db_transaction.atomic
    def executer(
        expediteur,
        recepteur,
        montant: Decimal,
        description: str = '',
    ) -> Transaction:

        # 🔒 Récupération des wallets avec lock
        try:
            wallet_exp = Wallet.objects.select_for_update().get(commercant=expediteur)
        except Wallet.DoesNotExist:
            raise ValidationError('Wallet expéditeur introuvable.')

        try:
            wallet_rec = Wallet.objects.select_for_update().get(commercant=recepteur)
        except Wallet.DoesNotExist:
            raise ValidationError('Wallet destinataire introuvable.')

        # ✅ Vérifications
        if wallet_exp.balance < montant:
            raise ValidationError('Solde insuffisant pour effectuer ce transfert.')

        # 🔄 Mouvements
        wallet_exp.debiter(montant)
        wallet_rec.crediter(montant)

        # 🧾 Enregistrement
        transaction = Transaction.objects.create(
            commercant=expediteur,
            wallet_expediteur=wallet_exp,
            wallet_recepteur=wallet_rec,
            montant=montant,
            frais=0,  # Toujours gratuit (INTERNE)
            type=Transaction.Type.INTERNE,
            statut=Transaction.Statut.SUCCESS,
            description=description or f'Transfert vers {recepteur.email}',
        )

        return transaction

    @staticmethod
    @db_transaction.atomic
    def annuler(transaction: Transaction, user) -> Transaction:
        if not transaction.is_annulable:
            raise ValidationError('Cette transaction ne peut pas être annulée.')

        if transaction.commercant != user:
            raise ValidationError('Non autorisé.')

        # 🔄 Remboursement
        wallet_exp = Wallet.objects.select_for_update().get(
            commercant=transaction.wallet_expediteur.commercant
        )
        wallet_rec = Wallet.objects.select_for_update().get(
            commercant=transaction.wallet_recepteur.commercant
        )

        wallet_rec.debiter(transaction.montant)
        wallet_exp.crediter(transaction.montant)

        transaction.statut = Transaction.Statut.CANCELLED
        transaction.save(update_fields=['statut', 'updated_at'])

        return transaction