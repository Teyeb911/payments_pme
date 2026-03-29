from django.db import models


class TimeStampedModel(models.Model):
    """Modèle abstrait avec timestamps automatiques."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
