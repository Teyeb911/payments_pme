from django.contrib import admin
from .models import BankSync, SyncLog


@admin.register(BankSync)
class BankSyncAdmin(admin.ModelAdmin):
    list_display = ['compte_externe', 'status', 'last_sync_at', 'last_successful_sync_at', 'is_active']
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['compte_externe__numero_compte', 'compte_externe__nom_banque']
    readonly_fields = ['last_sync_at', 'last_successful_sync_at', 'created_at', 'updated_at']
    ordering = ['-last_sync_at']


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['bank_sync', 'action', 'count', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['bank_sync__compte_externe__numero_compte', 'message']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
