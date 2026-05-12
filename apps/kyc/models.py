from django.db import models

from core.models import TimeStampedModel
from core.utils import generate_reference
from apps.users.models import User


class KycRecord(TimeStampedModel):

    class Status(models.TextChoices):
        PENDING  = 'pending',  'En attente'
        VERIFIED = 'verified', 'Vérifié'
        FAILED   = 'failed',   'Échoué'

    user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_records')
    kyc_id         = models.CharField(max_length=16, unique=True, editable=False)
    nni            = models.CharField(max_length=50)
    nom_fr         = models.CharField(max_length=100, blank=True)
    nom_ar         = models.CharField(max_length=100, blank=True)
    prenom_fr      = models.CharField(max_length=100, blank=True)
    prenom_ar      = models.CharField(max_length=100, blank=True)
    date_naissance = models.CharField(max_length=20, blank=True)
    lieu_naissance = models.CharField(max_length=150, blank=True)
    sexe           = models.CharField(max_length=10, blank=True)
    nationalite    = models.CharField(max_length=50, blank=True)
    face_verified  = models.BooleanField(default=False)
    confidence     = models.FloatField(default=0.0)
    status         = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.VERIFIED,
        db_index=True,
    )

    class Meta:
        db_table     = 'kyc_records'
        verbose_name = 'Enregistrement KYC'
        ordering     = ['-created_at']

    def __str__(self):
        return f'KYC {self.kyc_id} – {self.user}'

    def save(self, *args, **kwargs):
        if not self.kyc_id:
            self.kyc_id = generate_reference()
        super().save(*args, **kwargs)
