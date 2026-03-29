from django.conf import settings
from django.db import models
from core.models import TimeStampedModel


class Wallet(TimeStampedModel):

    commercant = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        limit_choices_to={'role': 'commercant'},
    )
    balance   = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency  = models.CharField(max_length=5, default='DZD')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table     = 'wallets'
        verbose_name = 'Wallet'

    def __str__(self) -> str:
        return f'Wallet({self.commercant.email}) — {self.balance} {self.currency}'

    # ── Business logic ──────────────────────────────
    def crediter(self, montant) -> None:
        if montant <= 0:
            raise ValueError('Le montant doit être positif.')
        self.balance += montant
        self.save(update_fields=['balance', 'updated_at'])

    def debiter(self, montant) -> None:
        if montant <= 0:
            raise ValueError('Le montant doit être positif.')
        if self.balance < montant:
            raise ValueError('Solde insuffisant.')
        self.balance -= montant
        self.save(update_fields=['balance', 'updated_at'])
