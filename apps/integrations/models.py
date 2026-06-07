from django.conf import settings
from django.db import models
from core.models import TimeStampedModel


class BankSync(TimeStampedModel):
    """Enregistre les derniers syncs pour chaque compte externe."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        SYNCING = 'syncing', 'En cours'
        SUCCESS = 'success', 'Succès'
        FAILED = 'failed', 'Échoué'

    compte_externe = models.OneToOneField(
        'comptes.CompteExterne',
        on_delete=models.CASCADE,
        related_name='bank_sync',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_successful_sync_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    next_sync_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'bank_syncs'
        verbose_name = 'Bank Sync'

    def __str__(self) -> str:
        return f'Sync {self.compte_externe.nom_banque} — {self.status}'


class SyncLog(TimeStampedModel):
    """Journal détaillé de chaque sync."""

    class Action(models.TextChoices):
        FETCH = 'fetch', 'Récupération'
        CREATE = 'create', 'Création'
        UPDATE = 'update', 'Mise à jour'
        ERROR = 'error', 'Erreur'

    bank_sync = models.ForeignKey(
        BankSync,
        on_delete=models.CASCADE,
        related_name='logs',
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    count = models.IntegerField(default=0)

    class Meta:
        db_table = 'sync_logs'
        verbose_name = 'Sync Log'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.action} — {self.bank_sync} ({self.created_at})'
