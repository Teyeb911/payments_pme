from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Transaction

User = get_user_model()


def _normalize_phone(value):
    # Chiffres uniquement, sans l'indicatif mauritanien (222 / 00222).
    digits = ''.join(ch for ch in str(value) if ch.isdigit())
    if digits.startswith('00222'):
        digits = digits[5:]
    elif digits.startswith('222') and len(digits) > 8:
        digits = digits[3:]
    return digits


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

        # Comparaison tolérante au format : "+222 45 25 00 00", "45250000"
        # et "0022245250000" désignent le même numéro.
        local = _normalize_phone(telephone)
        if len(local) < 8:
            raise serializers.ValidationError('Numero de telephone invalide.')
        # Filtre en Python : les numéros stockés peuvent contenir espaces/indicatif.
        candidats = User.objects.only('id', 'telephone').filter(
            role='commercant',
            is_active=True,
        )
        ids = [u.id for u in candidats if _normalize_phone(u.telephone or '') == local]
        recepteurs = User.objects.filter(id__in=ids)
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
