from rest_framework import serializers
from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    commercant_email = serializers.EmailField(source='commercant.email', read_only=True)
    commercant_nom   = serializers.CharField(source='commercant.nom',   read_only=True)

    class Meta:
        model        = Wallet
        fields       = [
            'id', 'commercant_email', 'commercant_nom',
            'balance', 'currency', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'balance', 'created_at', 'updated_at']


class ChargerWalletSerializer(serializers.Serializer):
    montant       = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1)
    id_compte_ext = serializers.IntegerField(help_text='ID du compte externe source')
