import secrets
import uuid

from django.db import models

from apps.users.models import User
from apps.wallets.models import Wallet


class MerchantPartner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    api_key = models.CharField(max_length=100, unique=True, blank=True)
    webhook_secret = models.CharField(max_length=100, blank=True)
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = "sk_live_" + secrets.token_urlsafe(16)
        if not self.webhook_secret:
            self.webhook_secret = "wh_secret_" + secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SubscriptionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(
        MerchantPartner,
        on_delete=models.CASCADE,
        related_name="plans",
    )
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["partner", "name"]

    def __str__(self):
        return f"{self.partner.name} - {self.name}"


class PaymentRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(MerchantPartner, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100)
    callback_url = models.URLField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.reference} - {self.status}"

    @property
    def amount(self):
        return self.plan.amount
