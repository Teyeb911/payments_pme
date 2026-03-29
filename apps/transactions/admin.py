from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display   = [
        'reference', 'commercant', 'type', 'montant',
        'frais', 'statut', 'created_at'
    ]
    list_filter    = ['type', 'statut', 'created_at']
    search_fields  = ['reference', 'commercant__email', 'description']
    readonly_fields = [
        'reference', 'frais', 'montant_total',
        'created_at', 'updated_at'
    ]
    ordering       = ['-created_at']

    def montant_total(self, obj):
        return obj.montant_total
    montant_total.short_description = 'Total (montant + frais)'
