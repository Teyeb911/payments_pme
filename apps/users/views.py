from django.contrib.auth import get_user_model
from rest_framework import generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
import random
from django.core.mail import send_mail
from django.core.cache import cache
from rest_framework.permissions import AllowAny
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

# ────────────────────

from rest_framework.permissions import AllowAny

class CheckEmailView(APIView):
    """POST — vérifie si un email existe déjà."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'detail': 'Email requis.'},
                            status=status.HTTP_400_BAD_REQUEST)

        exists = User.objects.filter(email=email).exists()

        if exists:
            return Response({'exists': True}, status=status.HTTP_200_OK)
        else:
            return Response({'exists': False}, status=status.HTTP_404_NOT_FOUND)


class SendVerificationCodeView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'success': False, 'error': 'Email requis'}, status=400)
        
        # Générer un code à 6 chiffres
        code = str(random.randint(100000, 999999))
        
        # Stocker le code dans cache (expire après 10 minutes)
        cache.set(f'verif_code_{email}', code, timeout=600)
        
        # Envoyer l'email
        try:
            send_mail(
                subject='🔐 Code de vérification - TrackPay',
                message=f'''
Bonjour,

Votre code de vérification TrackPay est : {code}

Ce code est valable pendant 10 minutes.

Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.

Cordialement,
L'équipe TrackPay
                ''',
                from_email='trackpay.platform@gmail.com',
                recipient_list=[email],
                fail_silently=False,
            )
            return Response({'success': True, 'message': 'Code envoyé avec succès'})
            
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500)


class VerifyCodeView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        
        if not email or not code:
            return Response({'success': False, 'error': 'Email et code requis'}, status=400)
        
        # Vérifier le code dans le cache
        stored_code = cache.get(f'verif_code_{email}')
        
        if stored_code and stored_code == code:
            # Code valide - on peut le supprimer
            cache.delete(f'verif_code_{email}')
            return Response({'success': True, 'message': 'Code valide'})
        
        return Response({'success': False, 'error': 'Code invalide ou expiré'}, status=400)
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
#  Reset Password (mot de passe oublié)
# ─────────────────────────────────────────────────────
class ForgotPasswordView(APIView):
    """
    POST { email } → envoie un code de réinitialisation
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'success': False, 'error': 'Email requis'},
                            status=400)

        # ✅ On ne révèle pas si l'email existe ou non (sécurité)
        user_exists = User.objects.filter(email=email).exists()
        if not user_exists:
            # Réponse identique pour éviter l'énumération d'emails
            return Response({'success': True,
                             'message': 'Si cet email existe, un code a été envoyé.'})

        code = str(random.randint(100000, 999999))
        cache.set(f'reset_code_{email}', code, timeout=600)

        try:
            send_mail(
                subject='🔑 Réinitialisation de mot de passe — TrackPay',
                message=f"""Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe TrackPay.

Votre code de réinitialisation est :

{code}

Ce code est valable pendant 10 minutes.
Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.

Cordialement,
L'équipe TrackPay""",
                from_email='trackpay.platform@gmail.com',
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500)

        return Response({'success': True,
                         'message': 'Si cet email existe, un code a été envoyé.'})


class VerifyResetCodeView(APIView):
    """
    POST { email, code } → valide le code sans changer le mot de passe
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        code  = request.data.get('code',  '').strip()

        if not email or not code:
            return Response({'success': False,
                             'error': 'Email et code requis'}, status=400)

        stored_code = cache.get(f'reset_code_{email}')
        if stored_code and stored_code == code:
            # On garde le code en cache pour la prochaine étape
            # mais on marque qu'il a été vérifié
            cache.set(f'reset_verified_{email}', True, timeout=600)
            return Response({'success': True, 'message': 'Code valide'})

        return Response({'success': False,
                         'error': 'Code invalide ou expiré'}, status=400)


class ResetPasswordView(APIView):
    """
    POST { email, code, new_password, new_password2 } → change le mot de passe
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email         = request.data.get('email', '').strip()
        code          = request.data.get('code',  '').strip()
        new_password  = request.data.get('new_password', '')
        new_password2 = request.data.get('new_password2', '')

        if not all([email, code, new_password, new_password2]):
            return Response({'success': False,
                             'error': 'Tous les champs sont requis'}, status=400)

        if new_password != new_password2:
            return Response({'success': False,
                             'error': 'Les mots de passe ne correspondent pas'},
                            status=400)

        if len(new_password) < 8:
            return Response({'success': False,
                             'error': 'Le mot de passe doit contenir au moins 8 caractères'},
                            status=400)

        # Vérifier que le code est valide
        stored_code = cache.get(f'reset_code_{email}')
        verified    = cache.get(f'reset_verified_{email}')

        if not (verified or (stored_code and stored_code == code)):
            return Response({'success': False,
                             'error': 'Code invalide ou expiré'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'success': False,
                             'error': 'Utilisateur introuvable'}, status=404)

        user.set_password(new_password)
        user.save()

        # Nettoyer le cache
        cache.delete(f'reset_code_{email}')
        cache.delete(f'reset_verified_{email}')

        return Response({'success': True,
                         'message': 'Mot de passe réinitialisé avec succès.'})


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