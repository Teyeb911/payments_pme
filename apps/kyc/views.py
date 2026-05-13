import logging

import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import success_response
from apps.users.models import User
from .models import KycRecord
from .serializers import KycCompleteSerializer

logger = logging.getLogger('kyc')


class KycAnalyzeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser]

    def post(self, request):
        image = request.FILES.get('image')
        if not image:
            return Response(
                {'success': False, 'message': 'Champ "image" requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info('KYC analyze – user=%s ip=%s', request.user.id, request.META.get('REMOTE_ADDR'))

        try:
            resp = requests.post(
                settings.KYC_AI_URL,
                headers={'X-API-Key': settings.KYC_AI_KEY},
                files={'file': (image.name, image.read(), image.content_type if image.content_type in ('image/jpeg', 'image/png') else 'image/jpeg')},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.Timeout:
            logger.error('KYC AI timeout – user=%s', request.user.id)
            return Response(
                {'success': False, 'message': 'Service KYC non disponible (timeout).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except requests.RequestException as exc:
            body = getattr(exc.response, 'text', '') if hasattr(exc, 'response') else ''
            logger.error('KYC AI error – user=%s err=%s body=%s', request.user.id, exc, body)
            return Response(
                {'success': False, 'message': 'Service KYC indisponible.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        raw  = resp.json()
        card = raw.get('data', {})

        result = {
            'nni':            card.get('identifier', ''),
            'nom_fr':         card.get('last_name_fl', ''),
            'nom_ar':         card.get('last_name_ll', ''),
            'prenom_fr':      card.get('first_name_fl', ''),
            'prenom_ar':      card.get('first_name_ll', ''),
            'date_naissance': card.get('birth_date', ''),
            'lieu_naissance': card.get('birth_place_fl', ''),
            'sexe':           card.get('gender', ''),
            'nationalite':    card.get('nationality', ''),
            'face_image':     card.get('face_image', ''),
        }

        return Response(success_response(data=result))


class KycCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = KycCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        card = data['card_data']

        user = request.user

        record = KycRecord.objects.create(
            user           = user,
            nni            = card['nni'],
            nom_fr         = card.get('nom_fr', ''),
            nom_ar         = card.get('nom_ar', ''),
            prenom_fr      = card.get('prenom_fr', ''),
            prenom_ar      = card.get('prenom_ar', ''),
            date_naissance = card.get('date_naissance', ''),
            lieu_naissance = card.get('lieu_naissance', ''),
            sexe           = card.get('sexe', ''),
            nationalite    = card.get('nationalite', ''),
            face_verified  = data['face_verified'],
            confidence     = data['confidence'],
            status         = KycRecord.Status.VERIFIED,
        )

        user.kyc_status = User.KycStatus.VERIFIED
        user.save(update_fields=['kyc_status'])

        logger.info(
            'KYC complete – user=%s kyc_id=%s face_verified=%s confidence=%.2f',
            user.id, record.kyc_id, data['face_verified'], data['confidence'],
        )

        return Response(
            {'success': True, 'kyc_id': record.kyc_id},
            status=status.HTTP_201_CREATED,
        )


class KycStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if not request.user.is_admin and request.user.id != user_id:
            return Response(
                {'success': False, 'message': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        target = get_object_or_404(User, id=user_id)
        latest = KycRecord.objects.filter(user=target).order_by('-created_at').first()

        return Response(success_response(data={
            'status': target.kyc_status,
            'date':   latest.created_at.isoformat() if latest else None,
        }))
