from rest_framework import serializers
from .models import BankSync, SyncLog


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = ['id', 'action', 'message', 'details', 'count', 'created_at']
        read_only_fields = ['id', 'created_at']


class BankSyncSerializer(serializers.ModelSerializer):
    logs = SyncLogSerializer(many=True, read_only=True)

    class Meta:
        model = BankSync
        fields = [
            'id', 'compte_externe', 'status', 'last_sync_at',
            'last_successful_sync_at', 'error_message', 'next_sync_at',
            'is_active', 'logs',
        ]
        read_only_fields = [
            'id', 'last_sync_at', 'last_successful_sync_at',
            'error_message', 'next_sync_at', 'logs',
        ]
