from django.contrib import admin
from .models import KycRecord


@admin.register(KycRecord)
class KycRecordAdmin(admin.ModelAdmin):
    list_display    = ['kyc_id', 'user', 'nni', 'nom_fr', 'prenom_fr', 'status', 'face_verified', 'confidence', 'created_at']
    list_filter     = ['status', 'face_verified', 'nationalite']
    search_fields   = ['kyc_id', 'nni', 'user__email', 'nom_fr', 'prenom_fr']
    readonly_fields = ['kyc_id', 'created_at', 'updated_at']
    ordering        = ['-created_at']

    actions = ['valider_kyc', 'rejeter_kyc']

    @admin.action(description='Valider les KYC sélectionnés')
    def valider_kyc(self, request, queryset):
        for record in queryset:
            record.status = KycRecord.Status.VERIFIED
            record.save(update_fields=['status'])
            record.user.kyc_status = 'verified'
            record.user.save(update_fields=['kyc_status'])
        self.message_user(request, f'{queryset.count()} KYC validé(s).')

    @admin.action(description='Rejeter les KYC sélectionnés')
    def rejeter_kyc(self, request, queryset):
        for record in queryset:
            record.status = KycRecord.Status.FAILED
            record.save(update_fields=['status'])
            record.user.kyc_status = 'failed'
            record.user.save(update_fields=['kyc_status'])
        self.message_user(request, f'{queryset.count()} KYC rejeté(s).')
