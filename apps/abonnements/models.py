from django.conf import settings
from django.db import models
from core.models import TimeStampedModel


class Plan(models.Model):
    """Plans d'abonnement disponibles sur la plateforme."""

    class Type(models.TextChoices):
        GRATUIT    = 'gratuit',    'Gratuit'
        BASIC      = 'basic',      'Basic'
        PRO        = 'pro',        'Pro'
        ENTERPRISE = 'enterprise', 'Enterprise'

    type          = models.CharField(max_length=20, choices=Type.choices, unique=True)
    prix_mensuel  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    description   = models.TextField(blank=True)
    nb_comptes_max = models.IntegerField(default=1, help_text='Nombre max de comptes externes')
    is_actif      = models.BooleanField(default=True)

    class Meta:
        db_table     = 'plans'
        verbose_name = 'Plan'

    def __str__(self) -> str:
        return f'{self.type} — {self.prix_mensuel} DZD/mois'


class Abonnement(TimeStampedModel):
    """Abonnement actif d'un commerçant à un plan."""

    class Statut(models.TextChoices):
        ACTIF    = 'actif',    'Actif'
        EXPIRE   = 'expiré',   'Expiré'
        RESILIÉ  = 'résilié',  'Résilié'

    commercant        = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='abonnement',
        limit_choices_to={'role': 'commercant'},
    )
    plan              = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='abonnements',
    )
    statut            = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.ACTIF,
        db_index=True,
    )
    date_debut        = models.DateField(auto_now_add=True)
    date_expiration   = models.DateField()
    auto_renouvellement = models.BooleanField(default=True)

    class Meta:
        db_table     = 'abonnements'
        verbose_name = 'Abonnement'

    def __str__(self) -> str:
        return f'{self.commercant.email} — {self.plan.type} ({self.statut})'

    @property
    def is_actif(self) -> bool:
        from django.utils import timezone
        return (
            self.statut == self.Statut.ACTIF
            and self.date_expiration >= timezone.now().date()
        )
