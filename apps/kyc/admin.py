from django.contrib import admin

from .models import KycRecord


@admin.register(KycRecord)
class KycRecordAdmin(admin.ModelAdmin):
    list_display    = ['kyc_id', 'user', 'nni', 'status', 'face_verified', 'confidence', 'created_at']
    list_filter     = ['status', 'face_verified', 'nationalite']
    search_fields   = ['kyc_id', 'nni', 'user__email', 'nom_fr', 'prenom_fr']
    readonly_fields = ['kyc_id', 'created_at', 'updated_at']
    ordering        = ['-created_at']
