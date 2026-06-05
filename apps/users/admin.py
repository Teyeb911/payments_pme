from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display    = ['email', 'nom', 'role', 'kyc_status', 'is_active', 'is_verified', 'created_at']
    list_filter     = ['role', 'kyc_status', 'is_active', 'is_verified']
    search_fields   = ['email', 'nom', 'telephone']
    ordering        = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None,            {'fields': ('email', 'password')}),
        ('Informations',  {'fields': ('nom', 'telephone', 'adresse')}),
        ('Rôle & Statut', {'fields': ('role', 'kyc_status', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions',   {'fields': ('groups', 'user_permissions')}),
        ('Dates',         {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'nom', 'password1', 'password2', 'role'),
        }),
    )

    actions = ['suspendre', 'activer', 'valider_kyc', 'rejeter_kyc']

    @admin.action(description='Suspendre les comptes sélectionnés')
    def suspendre(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f'{n} compte(s) suspendu(s).')

    @admin.action(description='Activer les comptes sélectionnés')
    def activer(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f'{n} compte(s) activé(s).')

    @admin.action(description='Valider le KYC')
    def valider_kyc(self, request, queryset):
        n = queryset.update(kyc_status=User.KycStatus.VERIFIED)
        self.message_user(request, f'KYC validé pour {n} commerçant(s).')

    @admin.action(description='Rejeter le KYC')
    def rejeter_kyc(self, request, queryset):
        n = queryset.update(kyc_status=User.KycStatus.FAILED)
        self.message_user(request, f'KYC rejeté pour {n} commerçant(s).')
