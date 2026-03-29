from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsCommerçant, IsOwnerOrAdmin
from core.utils import success_response
from .models import CompteExterne
from .serializers import (
    CompteExterneSerializer,
    CompteExterneCreateSerializer,
    PaiementEntrantSerializer,
)


class CompteListCreateView(generics.ListCreateAPIView):
    """
    GET  — liste des comptes externes du commerçant connecté.
    POST — lier un nouveau compte externe.
    """
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CompteExterneCreateSerializer
        return CompteExterneSerializer

    def get_queryset(self):
        return CompteExterne.objects.filter(
            commercant=self.request.user
        ).order_by('-created_at')


class CompteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — détail d'un compte.
    PATCH  — modifier (ex: api_token).
    DELETE — délier le compte.
    """
    serializer_class   = CompteExterneSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return CompteExterne.objects.filter(commercant=self.request.user)

    def destroy(self, request, *args, **kwargs):
        compte = self.get_object()
        compte.is_actif = False
        compte.save(update_fields=['is_actif'])
        return Response(
            success_response(message='Compte délié avec succès.'),
            status=status.HTTP_200_OK,
        )


class PaiementsEntrantsView(APIView):
    """
    GET — récupère les paiements entrants depuis le compte externe.
    (Simulation — à remplacer par l'API bancaire réelle)
    """
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get(self, request, pk):
        compte = get_object_or_404(
            CompteExterne,
            id=pk,
            commercant=request.user,
            is_actif=True,
        )

        # ── Simulation paiements entrants ──
        # En production : appel API bancaire avec compte.api_token
        paiements = [
            {
                'reference':  'PAY-001',
                'montant':    15000.00,
                'date':       '2025-03-01T10:00:00Z',
                'expediteur': 'Client A',
                'description': 'Paiement commande #101',
            },
            {
                'reference':  'PAY-002',
                'montant':    8500.00,
                'date':       '2025-03-02T14:30:00Z',
                'expediteur': 'Client B',
                'description': 'Règlement facture #55',
            },
        ]

        serializer = PaiementEntrantSerializer(paiements, many=True)
        return Response(success_response(data={
            'compte': compte.nom_banque,
            'paiements': serializer.data,
        }))
