from rest_framework import serializers
from .models import CompteExterne


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
