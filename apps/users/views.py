from django.contrib.auth import get_user_model
from rest_framework import generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import IsAdmin
from core.utils import success_response
from .serializers import (
    AdminUserSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


# ─────────────────────────────────────────────────────
#  Register
# ─────────────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user   = serializer.save()
        tokens = RefreshToken.for_user(user)
        return Response(
            success_response(
                data={
                    'user':    UserSerializer(user).data,
                    'refresh': str(tokens),
                    'access':  str(tokens.access_token),
                },
                message='Compte créé avec succès.',
            ),
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────
#  Login / Logout / Refresh
# ─────────────────────────────────────────────────────
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class   = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data.get('refresh')).blacklist()
            return Response(success_response(message='Déconnexion réussie.'))
        except Exception:
            return Response(
                {'success': False, 'message': 'Token invalide ou déjà expiré.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ─────────────────────────────────────────────────────
#  Profile — /me
# ─────────────────────────────────────────────────────
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(success_response(data=UserSerializer(request.user).data))

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(success_response(
            data=UserSerializer(request.user).data,
            message='Profil mis à jour.',
        ))


# ─────────────────────────────────────────────────────
#  Change password
# ─────────────────────────────────────────────────────
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(success_response(message='Mot de passe modifié avec succès.'))


# ─────────────────────────────────────────────────────
#  Admin — Gestion des commerçants
# ─────────────────────────────────────────────────────
class UserListView(generics.ListAPIView):
    queryset           = User.objects.filter(role='commercant').order_by('-created_at')
    serializer_class   = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['email', 'nom', 'telephone']
    ordering_fields    = ['created_at', 'nom']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = User.objects.filter(role='commercant')
    serializer_class   = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
