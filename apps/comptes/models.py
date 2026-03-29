from django.conf import settings
from django.db import models
from core.models import TimeStampedModel


class CompteExterne(TimeStampedModel):

    class TypeCompte(models.TextChoices):
        BANCAIRE  = 'bancaire',  'Compte Bancaire'
        CCP       = 'ccp',       'CCP / Poste'
        MOBILE    = 'mobile',    'Paiement Mobile'
        AUTRE     = 'autre',     'Autre'

    commercant     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comptes_externes',
        limit_choices_to={'role': 'commercant'},
    )
    nom_banque     = models.CharField(max_length=100)
    type_compte    = models.CharField(
        max_length=20,
        choices=TypeCompte.choices,
        default=TypeCompte.BANCAIRE,
    )
    numero_compte  = models.CharField(max_length=50)
    api_token      = models.TextField(blank=True, help_text='Token d\'intégration API bancaire')
    is_actif       = models.BooleanField(default=True)

    class Meta:
        db_table     = 'comptes_externes'
        verbose_name = 'Compte Externe'
        unique_together = [['commercant', 'numero_compte']]

    def __str__(self) -> str:
        return f'{self.nom_banque} — {self.numero_compte} ({self.commercant.email})'
