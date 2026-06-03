from django.contrib import admin
from .models import CompteExterne, TransactionExterne


@admin.register(CompteExterne)
class CompteExterneAdmin(admin.ModelAdmin):
    list_display  = ['commercant', 'nom_banque', 'type_compte', 'numero_compte', 'is_actif', 'created_at']
    list_filter   = ['type_compte', 'is_actif']
    search_fields = ['commercant__email', 'nom_banque', 'numero_compte']
    ordering      = ['-created_at']


@admin.register(TransactionExterne)
class TransactionExterneAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'compte_externe', 'montant', 'type_transaction', 'statut', 'date']
    list_filter   = ['type_transaction', 'statut', 'date']
    search_fields = ['reference', 'description', 'compte_externe__numero_compte']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    ordering      = ['-date']
