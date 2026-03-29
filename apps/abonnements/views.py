from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from core.permissions import IsAdmin, IsCommerçant
from core.utils import success_response
from .models import Abonnement, Plan
from .serializers import AbonnementSerializer, PlanSerializer, SouscrireSerializer
from .services import AbonnementService


# ─────────────────────────────────────────────────────
#  Plans disponibles (public)
# ─────────────────────────────────────────────────────
class PlanListView(generics.ListAPIView):
    """GET — liste des plans disponibles."""
    queryset           = Plan.objects.filter(is_actif=True).order_by('prix_mensuel')
    serializer_class   = PlanSerializer
    permission_classes = [IsAuthenticated]


# ─────────────────────────────────────────────────────
#  Mon abonnement
# ─────────────────────────────────────────────────────
class MonAbonnementView(APIView):
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get(self, request):
        """GET — abonnement actuel du commerçant."""
        abo = get_object_or_404(Abonnement, commercant=request.user)
        return Response(success_response(data=AbonnementSerializer(abo).data))


class SouscrireView(APIView):
    """POST — souscrire ou changer de plan."""
    permission_classes = [IsAuthenticated, IsCommerçant]

    def post(self, request):
        serializer = SouscrireSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            abo = AbonnementService.souscrire(
                commercant          = request.user,
                plan_type           = serializer.validated_data['plan_type'],
                auto_renouvellement = serializer.validated_data['auto_renouvellement'],
            )
        except Plan.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Plan introuvable ou inactif.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            success_response(
                data=AbonnementSerializer(abo).data,
                message='Abonnement souscrit avec succès.',
            ),
            status=status.HTTP_200_OK,
        )


class ResilierView(APIView):
    """POST — résilier l'abonnement."""
    permission_classes = [IsAuthenticated, IsCommerçant]

    def post(self, request):
        abo = get_object_or_404(Abonnement, commercant=request.user)

        if abo.statut == Abonnement.Statut.RESILIÉ:
            return Response(
                {'success': False, 'message': 'Abonnement déjà résilié.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        abo = AbonnementService.resilier(abo)
        return Response(success_response(
            data=AbonnementSerializer(abo).data,
            message='Abonnement résilié.',
        ))


class RenouvelerView(APIView):
    """POST — renouveler manuellement."""
    permission_classes = [IsAuthenticated, IsCommerçant]

    def post(self, request):
        abo = get_object_or_404(Abonnement, commercant=request.user)
        abo = AbonnementService.renouveler(abo)
        return Response(success_response(
            data=AbonnementSerializer(abo).data,
            message='Abonnement renouvelé pour 1 mois.',
        ))


# ─────────────────────────────────────────────────────
#  Admin
# ─────────────────────────────────────────────────────
class AllAbonnementsView(generics.ListAPIView):
    """GET (admin) — tous les abonnements."""
    queryset           = Abonnement.objects.select_related('commercant', 'plan').order_by('-created_at')
    serializer_class   = AbonnementSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    search_fields      = ['commercant__email', 'plan__type']
    filterset_fields   = ['statut', 'plan__type']
