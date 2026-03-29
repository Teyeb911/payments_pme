from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['email', 'nom', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter    = ['role', 'is_verified', 'is_active']
    search_fields  = ['email', 'nom']
    ordering       = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None,            {'fields': ('email', 'password')}),
        ('Informations',  {'fields': ('nom', 'telephone', 'adresse')}),
        ('Rôle & Statut', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions',   {'fields': ('groups', 'user_permissions')}),
        ('Dates',         {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'nom', 'password1', 'password2', 'role'),
        }),
    )
