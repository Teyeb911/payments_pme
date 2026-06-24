import secrets

from django.contrib import admin

from .models import MerchantPartner, PaymentRequest, SubscriptionPlan


@admin.register(MerchantPartner)
class MerchantPartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "api_key", "is_active", "created_at")
    readonly_fields = ("api_key", "webhook_secret")
    actions = ("regenerate_api_key",)

    @admin.action(description="Regenerate API Key")
    def regenerate_api_key(self, request, queryset):
        for partner in queryset:
            partner.api_key = "sk_live_" + secrets.token_urlsafe(16)
            partner.save(update_fields=["api_key"])


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ("partner", "amount", "status", "reference", "payer", "created_at", "paid_at")
    list_filter = ("status", "partner")

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("partner", "name", "amount", "period", "is_active", "created_at")
    list_filter = ("partner", "is_active", "period")
