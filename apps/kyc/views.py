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


def _call_primary_ocr(url, api_key, filename, image_bytes, mime_type, user_id, log):
    try:
        resp = requests.post(
            url,
            headers={'X-API-Key': api_key},
            files={'id_card': (filename, image_bytes, mime_type)},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.Timeout:
        log.error('KYC primary timeout – user=%s', user_id)
    except requests.RequestException as exc:
        body = getattr(exc.response, 'text', '') if hasattr(exc, 'response') else ''
        log.error('KYC primary error – user=%s err=%s body=%s', user_id, exc, body)
    return None


def _call_fallback_ocr(url, filename, image_bytes, mime_type, user_id, log):
    try:
        resp = requests.post(
            url,
            files={'id_card': (filename, image_bytes, mime_type)},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.Timeout:
        log.error('KYC fallback timeout – user=%s', user_id)
    except requests.RequestException as exc:
        body = getattr(exc.response, 'text', '') if hasattr(exc, 'response') else ''
        log.error('KYC fallback error – user=%s err=%s body=%s', user_id, exc, body)
    return None


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

        mime_type   = image.content_type if image.content_type in ('image/jpeg', 'image/png') else 'image/jpeg'
        image_bytes = image.read()

        # ── Service primaire ───────────────────────────────────────────────
        raw = _call_primary_ocr(settings.KYC_AI_URL, settings.KYC_AI_KEY,
                                 image.name, image_bytes, mime_type,
                                 request.user.id, logger)

        # ── Fallback si le service primaire a échoué ───────────────────────
        if raw is None:
            logger.info('KYC analyze – bascule sur le service de secours – user=%s', request.user.id)
            raw = _call_fallback_ocr(settings.KYC_AI_FALLBACK_URL,
                                     image.name, image_bytes, mime_type,
                                     request.user.id, logger)

        if raw is None:
            return Response(
                {'success': False, 'message': 'Tous les services KYC sont indisponibles.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        card = raw.get('data', raw)

        result = {
            'nni':            card.get('identifier', card.get('nni', '')),
            'nom_fr':         card.get('last_name_fl', card.get('nom_fr', '')),
            'nom_ar':         card.get('last_name_ll', card.get('nom_ar', '')),
            'prenom_fr':      card.get('first_name_fl', card.get('prenom_fr', '')),
            'prenom_ar':      card.get('first_name_ll', card.get('prenom_ar', '')),
            'date_naissance': card.get('birth_date', card.get('date_naissance', '')),
            'lieu_naissance': card.get('birth_place_fl', card.get('lieu_naissance', '')),
            'sexe':           card.get('gender', card.get('sexe', '')),
            'nationalite':    card.get('nationality', card.get('nationality_iso', card.get('nationalite', ''))),
            'face_image':     card.get('face_image', card.get('images', {}).get('base64', '')),
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


class KycValiderView(APIView):
    """POST — validation manuelle du KYC par un admin."""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not request.user.is_admin:
            return Response(
                {'success': False, 'message': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        target = get_object_or_404(User, id=user_id)
        record = KycRecord.objects.filter(user=target).order_by('-created_at').first()
        if record:
            record.status = KycRecord.Status.VERIFIED
            record.save(update_fields=['status'])
        target.kyc_status = User.KycStatus.VERIFIED
        target.save(update_fields=['kyc_status'])
        logger.info('KYC manual validation – admin=%s target=%s', request.user.id, user_id)
        return Response(success_response(message=f'KYC validé pour {target.email}.'))


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
