from django.contrib import admin
from .models import Plan, Abonnement


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display  = ['type', 'prix_mensuel', 'nb_comptes_max', 'is_actif']
    list_editable = ['prix_mensuel', 'is_actif']
    ordering      = ['prix_mensuel']


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display  = ['commercant', 'plan', 'statut', 'date_debut', 'date_expiration', 'auto_renouvellement']
    list_filter   = ['statut', 'plan__type', 'auto_renouvellement']
    search_fields = ['commercant__email']
    readonly_fields = ['date_debut', 'created_at', 'updated_at']
    ordering      = ['-created_at']
