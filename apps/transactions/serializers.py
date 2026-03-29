from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Transaction

User = get_user_model()


class TransactionSerializer(serializers.ModelSerializer):
    commercant_email  = serializers.EmailField(source='commercant.email', read_only=True)
    expediteur_email  = serializers.EmailField(source='wallet_expediteur.commercant.email', read_only=True)
    recepteur_email   = serializers.EmailField(source='wallet_recepteur.commercant.email',  read_only=True)
    montant_total     = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True, source='montant_total'
    )

    class Meta:
        model  = Transaction
        fields = [
            'id', 'reference',
            'commercant_email', 'expediteur_email', 'recepteur_email',
            'montant', 'frais', 'montant_total',
            'type', 'statut', 'description',
            'created_at',
        ]
        read_only_fields = ['id', 'reference', 'frais', 'statut', 'created_at']


# ── Transfert interne ─────────────────────────────────
class TransfertInterneSerializer(serializers.Serializer):
    email_recepteur = serializers.EmailField(
        help_text='Email du commerçant destinataire'
    )
    montant     = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_email_recepteur(self, value: str) -> str:
        try:
            recepteur = User.objects.get(email=value, role='commercant', is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError('Commerçant destinataire introuvable.')

        if recepteur == self.context['request'].user:
            raise serializers.ValidationError('Impossible de se transférer à soi-même.')

        self._recepteur = recepteur
        return value

    def get_recepteur(self):
        return self._recepteur


# ── Dashboard stats ───────────────────────────────────
class DashboardSerializer(serializers.Serializer):
    wallet_balance     = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_envoye       = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_recu         = serializers.DecimalField(max_digits=15, decimal_places=2)
    nb_transactions    = serializers.IntegerField()
    dernières_transactions = TransactionSerializer(many=True)
