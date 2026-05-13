from rest_framework import serializers

from .models import KycRecord


class CardDataSerializer(serializers.Serializer):
    nni            = serializers.CharField()
    nom_fr         = serializers.CharField(allow_blank=True, default='')
    nom_ar         = serializers.CharField(allow_blank=True, default='')
    prenom_fr      = serializers.CharField(allow_blank=True, default='')
    prenom_ar      = serializers.CharField(allow_blank=True, default='')
    date_naissance = serializers.CharField(allow_blank=True, default='')
    lieu_naissance = serializers.CharField(allow_blank=True, default='')
    sexe           = serializers.CharField(allow_blank=True, default='')
    nationalite    = serializers.CharField(allow_blank=True, default='')


class KycCompleteSerializer(serializers.Serializer):
    user_id       = serializers.CharField()
    card_data     = CardDataSerializer()
    face_verified = serializers.BooleanField()
    confidence    = serializers.FloatField(min_value=0.0, max_value=100.0)


class KycRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model  = KycRecord
        fields = [
            'kyc_id', 'nni', 'nom_fr', 'nom_ar', 'prenom_fr', 'prenom_ar',
            'date_naissance', 'lieu_naissance', 'sexe', 'nationalite',
            'face_verified', 'confidence', 'status', 'created_at',
        ]
