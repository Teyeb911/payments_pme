from django.conf import settings
from django.db import models
from core.models import TimeStampedModel


class DeviceToken(TimeStampedModel):
    """Jeton FCM d'un appareil, utilisé pour les notifications de virement."""

    class Platform(models.TextChoices):
        ANDROID = 'android', 'Android'
        IOS = 'ios', 'iOS'
        WEB = 'web', 'Web'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='device_tokens'
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.ANDROID)

    class Meta:
        verbose_name = 'Jeton appareil'
        verbose_name_plural = 'Jetons appareils'

    def __str__(self):
        return f'{self.user} · {self.platform}'
