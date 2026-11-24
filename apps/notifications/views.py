from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import success_response
from .models import DeviceToken


class DeviceTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(
        choices=DeviceToken.Platform.choices, default=DeviceToken.Platform.ANDROID
    )


class DeviceTokenView(APIView):
    """POST : enregistre le jeton FCM de l'appareil. DELETE : le retire (déconnexion)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = DeviceTokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        # Un jeton appartient à un seul compte : il suit le dernier utilisateur connecté.
        DeviceToken.objects.update_or_create(
            token=s.validated_data['token'],
            defaults={'user': request.user, 'platform': s.validated_data['platform']},
        )
        return Response(success_response(message='Appareil enregistré'), status=status.HTTP_200_OK)

    def delete(self, request):
        token = request.data.get('token', '')
        DeviceToken.objects.filter(user=request.user, token=token).delete()
        return Response(success_response(message='Appareil retiré'), status=status.HTTP_200_OK)
