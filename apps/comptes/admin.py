from django.contrib import admin
from .models import CompteExterne


@admin.register(CompteExterne)
class CompteExterneAdmin(admin.ModelAdmin):
    list_display  = ['commercant', 'nom_banque', 'type_compte', 'numero_compte', 'is_actif', 'created_at']
    list_filter   = ['type_compte', 'is_actif']
    search_fields = ['commercant__email', 'nom_banque', 'numero_compte']
    ordering      = ['-created_at']
