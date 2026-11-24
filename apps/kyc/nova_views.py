"""Endpoints TrackPay → NovaKYC (la clé API reste côté serveur)."""
import logging

from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import nova

logger = logging.getLogger(__name__)

_MAX_BYTES = 8 * 1024 * 1024  # 8 Mo par image


class NovaStatusView(APIView):
    """GET — l'app choisit le parcours NovaKYC seulement s'il est disponible."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'success': True, 'available': nova.is_available()})


class NovaVerifyView(APIView):
    """POST multipart : document (photo de la carte), selfie, face (optionnel :
    visage découpé de la carte). Renvoie la décision NovaKYC."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        document = request.FILES.get('document')
        selfie = request.FILES.get('selfie')
        face = request.FILES.get('face')
        if not document or not selfie:
            return Response(
                {'success': False, 'code': 'MISSING_IMAGES',
                 'message': 'Photo de la carte et selfie requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for f in (document, selfie, face):
            if f is not None and f.size > _MAX_BYTES:
                return Response(
                    {'success': False, 'code': 'IMAGE_TOO_LARGE',
                     'message': 'Image trop lourde (8 Mo max).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        ip = (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
              or request.META.get('REMOTE_ADDR', ''))
        try:
            result = nova.full_verification(
                document_b64=nova.b64(document),
                selfie_b64=nova.b64(selfie),
                face_b64=nova.b64(face) if face else None,
                client_ip=ip,
            )
        except nova.NovaUnavailable as exc:
            logger.warning('NovaKYC indisponible : %s', exc)
            return Response(
                {'success': False, 'code': 'NOVA_UNAVAILABLE',
                 'message': 'Service de vérification indisponible.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except nova.NovaError as exc:
            logger.error('NovaKYC erreur : %s', exc)
            return Response(
                {'success': False, 'code': 'NOVA_ERROR', 'message': str(exc.detail)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        logger.info(
            'NovaKYC user=%s passed=%s reasons=%s similarity=%.2f liveness=%.2f',
            request.user.id, result['kyc_passed'], result['rejection_reasons'],
            result['similarity'], result['liveness_score'],
        )
        return Response({'success': True, 'data': result})
