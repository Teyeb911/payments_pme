from django.conf import settings
from django.db import models
from core.models import TimeStampedModel
from core.utils import generate_reference


class Transaction(TimeStampedModel):

    class Type(models.TextChoices):
        INTERNE     = 'interne',     'Transfert Interne'
        EXTERNE     = 'externe',     'Paiement Externe'
        CHARGEMENT  = 'chargement',  'Chargement Wallet'

    class Statut(models.TextChoices):
        PENDING   = 'pending',   'En attente'
        SUCCESS   = 'success',   'Succès'
        FAILED    = 'failed',    'Échoué'
        CANCELLED = 'cancelled', 'Annulé'

    # ── Relations ────────────────────────────────────
    commercant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions',
        limit_choices_to={'role': 'commercant'},
    )
    wallet_expediteur = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.PROTECT,
        related_name='transactions_emises',
    )
    wallet_recepteur = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.PROTECT,
        related_name='transactions_recues',
    )
    compte_externe = models.ForeignKey(
        'comptes.CompteExterne',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
    )

    # ── Montants ─────────────────────────────────────
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    frais   = models.DecimalField(max_digits=8,  decimal_places=2, default=0)

    # ── Metadata ─────────────────────────────────────
    type        = models.CharField(max_length=20, choices=Type.choices, db_index=True)
    statut      = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PENDING, db_index=True)
    reference   = models.CharField(max_length=64, unique=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table     = 'transactions'
        verbose_name = 'Transaction'
        ordering     = ['-created_at']

    def __str__(self) -> str:
        return f'[{self.type}] {self.reference} — {self.montant} ({self.statut})'

    # ── Save hook ────────────────────────────────────
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference()
        # Transactions internes toujours gratuites
        if self.type == self.Type.INTERNE:
            self.frais = 0
        super().save(*args, **kwargs)

    # ── Properties ───────────────────────────────────
    @property
    def montant_total(self):
        return self.montant + self.frais

    @property
    def is_annulable(self) -> bool:
        return self.statut == self.Statut.PENDING
