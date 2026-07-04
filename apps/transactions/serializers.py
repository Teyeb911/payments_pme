from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Transaction

User = get_user_model()


class TransactionSerializer(serializers.ModelSerializer):
    commercant_telephone = serializers.CharField(source='commercant.telephone', read_only=True)
    expediteur_telephone = serializers.CharField(source='wallet_expediteur.commercant.telephone', read_only=True)
    recepteur_telephone = serializers.CharField(source='wallet_recepteur.commercant.telephone', read_only=True)
    montant_total = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id', 'reference',
            'commercant_telephone', 'expediteur_telephone', 'recepteur_telephone',
            'montant', 'frais', 'montant_total',
            'type', 'statut', 'description',
            'created_at',
        ]
        read_only_fields = ['id', 'reference', 'frais', 'statut', 'created_at']


class TransfertInterneSerializer(serializers.Serializer):
    telephone_recepteur = serializers.CharField(
        max_length=20,
        help_text='Numero de telephone du commercant destinataire',
    )
    montant = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_telephone_recepteur(self, value: str) -> str:
        telephone = value.strip()
        if not telephone:
            raise serializers.ValidationError('Numero de telephone requis.')

        recepteurs = User.objects.filter(
            telephone=telephone,
            role='commercant',
            is_active=True,
        )
        count = recepteurs.count()
        if count == 0:
            raise serializers.ValidationError('Commercant destinataire introuvable.')
        if count > 1:
            raise serializers.ValidationError(
                'Plusieurs commercants utilisent ce numero de telephone.'
            )

        recepteur = recepteurs.first()
        if recepteur == self.context['request'].user:
            raise serializers.ValidationError('Impossible de se transferer a soi-meme.')

        self._recepteur = recepteur
        return telephone

    def get_recepteur(self):
        return self._recepteur


class DashboardSerializer(serializers.Serializer):
    wallet_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_envoye = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_recu = serializers.DecimalField(max_digits=15, decimal_places=2)
    nb_transactions = serializers.IntegerField()
    dernieres_transactions = TransactionSerializer(many=True)
