from django.contrib import admin
from .models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display   = ['commercant', 'balance', 'currency', 'is_active', 'updated_at']
    list_filter    = ['currency', 'is_active']
    search_fields  = ['commercant__email', 'commercant__nom']
    readonly_fields = ['balance', 'created_at', 'updated_at']
    ordering       = ['-updated_at']
