from rest_framework import serializers
from .models import Abonnement, Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Plan
        fields = ['id', 'type', 'prix_mensuel', 'description', 'nb_comptes_max']


class AbonnementSerializer(serializers.ModelSerializer):
    plan              = PlanSerializer(read_only=True)
    commercant_email  = serializers.EmailField(source='commercant.email', read_only=True)
    is_actif          = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Abonnement
        fields = [
            'id', 'commercant_email', 'plan',
            'statut', 'is_actif',
            'date_debut', 'date_expiration',
            'auto_renouvellement', 'created_at',
        ]
        read_only_fields = ['id', 'statut', 'date_debut', 'created_at']


class SouscrireSerializer(serializers.Serializer):
    plan_type           = serializers.ChoiceField(choices=Plan.Type.choices)
    auto_renouvellement = serializers.BooleanField(default=True)
