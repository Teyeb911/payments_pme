from django.contrib import admin

from .models import InteropPartner, InteropTransaction


@admin.register(InteropPartner)
class InteropPartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "partner_code", "partner_key", "is_active", "created_at"]
    readonly_fields = ["partner_key", "shared_secret"]
    search_fields = ["name", "partner_code", "partner_key"]
    list_filter = ["is_active", "created_at"]


@admin.register(InteropTransaction)
class InteropTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "partner",
        "receiver",
        "amount",
        "sender_name",
        "reference",
        "status",
        "created_at",
    ]
    list_filter = ["status", "partner"]
    search_fields = ["reference", "receiver__email", "sender_name", "partner__name"]
    readonly_fields = [
        "id",
        "partner",
        "receiver",
        "amount",
        "sender_name",
        "reference",
        "status",
        "created_at",
    ]
