from rest_framework import serializers

from core.utils import generate_reference
from .models import CompteExterne, TransactionExterne


class CompteExterneSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CompteExterne
        fields = [
            'id', 'nom_banque', 'type_compte',
            'numero_compte', 'is_actif', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CompteExterneCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CompteExterne
        fields = ['nom_banque', 'type_compte', 'numero_compte', 'api_token']

    def create(self, validated_data):
        validated_data['commercant'] = self.context['request'].user
        return super().create(validated_data)


class PaiementEntrantSerializer(serializers.Serializer):
    """Représente un paiement entrant simulé depuis une banque externe."""
    reference  = serializers.CharField()
    montant    = serializers.DecimalField(max_digits=15, decimal_places=2)
    date       = serializers.DateTimeField()
    expediteur = serializers.CharField()
    description = serializers.CharField(required=False)


class TransactionExterneSerializer(serializers.ModelSerializer):
    compte_nom_banque = serializers.CharField(source='compte_externe.nom_banque', read_only=True)

    class Meta:
        model = TransactionExterne
        fields = [
            'id', 'compte_externe', 'compte_nom_banque', 'montant',
            'type_transaction', 'description', 'date', 'statut',
            'reference', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class TransactionExterneCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionExterne
        fields = ['montant', 'type_transaction', 'description', 'date']

    def create(self, validated_data):
        compte_externe = self.context['compte_externe']
        validated_data['reference'] = f"EXT-{generate_reference()}"
        validated_data['compte_externe'] = compte_externe
        return super().create(validated_data)
