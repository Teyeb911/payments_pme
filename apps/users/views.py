from decouple import config
from django.contrib.auth import get_user_model
from rest_framework import generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
import random
from django.shortcuts import redirect as django_redirect, get_object_or_404
from core.email import send_email, send_email_async
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
        
        send_email_async(
            to=email,
            subject='Code de vérification - TrackPay',
            body=f'Bonjour,\n\nVotre code de vérification TrackPay est : {code}\n\nCe code est valable pendant 10 minutes.\n\nSi vous n\'êtes pas à l\'origine de cette demande, ignorez cet email.\n\nCordialement,\nL\'équipe TrackPay',
        )
        return Response({'success': True, 'message': 'Code envoyé avec succès'})


class VerifyCodeView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        
        if not email or not code:
            return Response({'success': False, 'error': 'Email et code requis'}, status=400)
        
        stored_code = cache.get(f'verif_code_{email}')
        if stored_code and stored_code == code:
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


import requests
from django.shortcuts import redirect as django_redirect


class SSOCallbackView(APIView):
    permission_classes = [AllowAny]

    SSO_TOKEN_URL    = 'https://sso-backend-6b1e.onrender.com/o/token/'
    SSO_USERINFO_URL = 'https://sso-backend-6b1e.onrender.com/o/userinfo/'
    CLIENT_ID        = config('SSO_CLIENT_ID',     default='w25QcB0B9UAQ7t8kXwBqMPf7lR7vMshQtKb8CVhk')
    CLIENT_SECRET    = config('SSO_CLIENT_SECRET', default='')
    REDIRECT_URI     = config('SSO_REDIRECT_URI',  default='https://config-ap28-1mhk.onrender.com/sso/callback/')

    def get(self, request):
        code          = request.GET.get('code')
        error         = request.GET.get('error')
        code_verifier = request.GET.get('code_verifier', '')

        if error or not code:
            return Response({
                'success': False,
                'error': error or 'no_code'
            }, status=400)

        try:
            # ① Échanger code → access_token SSO
            token_data = {
                'grant_type':   'authorization_code',
                'code':         code,
                'redirect_uri': self.REDIRECT_URI,
                'client_id':    self.CLIENT_ID,
            }
            if self.CLIENT_SECRET:
                token_data['client_secret'] = self.CLIENT_SECRET
            if code_verifier:
                token_data['code_verifier'] = code_verifier

            token_res = requests.post(
                self.SSO_TOKEN_URL,
                data=token_data,
                timeout=10,
            )
            token_res.raise_for_status()
            sso_access = token_res.json()['access_token']

            # ② Récupérer le profil SSO
            user_res = requests.get(
                self.SSO_USERINFO_URL,
                headers={'Authorization': f'Bearer {sso_access}'},
                timeout=10,
            )
            user_res.raise_for_status()
            sso_user = user_res.json()

            email = sso_user.get('email', '').strip()
            nom = f"{sso_user.get('given_name', '')} {sso_user.get('family_name', '')}".strip()

            if not email:
                raise ValueError('Email SSO introuvable')

            # ③ Login ou Register sur TrackPay
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'nom': nom or email.split('@')[0],
                    'telephone': sso_user.get('phone', ''),
                    'adresse': '',
                    'role': 'commercant',
                    'is_active': True,
                },
            )

            if created:
                sso_pass = f'SSOTrackPay_{abs(hash(email))}'
                user.set_password(sso_pass)
                user.save()

                try:
                    from apps.wallets.models import Wallet
                    Wallet.objects.get_or_create(commercant=user)
                except Exception:
                    pass

                try:
                    from apps.abonnements.services import AbonnementService
                    AbonnementService.souscrire(user, 'gratuit', False)
                except Exception:
                    pass

            # ④ Générer JWT TrackPay
            tokens = RefreshToken.for_user(user)
            access = str(tokens.access_token)
            refresh = str(tokens)

            # ✅ Retourner les tokens en JSON (pas de redirection)
            return Response({
                'success': True,
                'access': access,
                'refresh': refresh,
                'email': email
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
class SSOLoginView(APIView):
    """
    POST { email } → connexion directe pour utilisateurs SSO vérifiés
    Appelé uniquement après vérification du token SSO côté Flutter
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'detail': 'Email requis.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)

        tokens = RefreshToken.for_user(user)
        return Response({
            'access':  str(tokens.access_token),
            'refresh': str(tokens),
            'user':    UserSerializer(user).data,
        })


            
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

        send_email_async(
            to=email,
            subject='Réinitialisation de mot de passe — TrackPay',
            body=f'Bonjour,\n\nVous avez demandé la réinitialisation de votre mot de passe TrackPay.\n\nVotre code de réinitialisation est :\n\n{code}\n\nCe code est valable pendant 10 minutes.\nSi vous n\'êtes pas à l\'origine de cette demande, ignorez cet email.\n\nCordialement,\nL\'équipe TrackPay',
        )
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


class CommercantDetailCompletView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        from .serializers import CommercantDetailSerializer
        user = get_object_or_404(User, pk=pk, role=User.Role.COMMERCANT)
        return Response(success_response(data=CommercantDetailSerializer(user).data))


class CommercantSuspendreView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, role=User.Role.COMMERCANT)
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response(success_response(message=f'Commerçant {user.email} suspendu.'))


class CommercantActiverView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, role=User.Role.COMMERCANT)
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response(success_response(message=f'Commerçant {user.email} activé.'))


class CommercantInvaliderView(APIView):
    """
    POST — invalide définitivement le compte d'un commerçant :
      1. désactive le compte (is_active = False)
      2. blackliste tous ses tokens JWT → déconnexion forcée immédiate
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        from rest_framework_simplejwt.token_blacklist.models import (
            OutstandingToken, BlacklistedToken
        )
        user = get_object_or_404(User, pk=pk, role=User.Role.COMMERCANT)

        if not user.is_active:
            return Response(
                {'success': False, 'message': 'Ce compte est déjà invalide.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = False
        user.save(update_fields=['is_active'])

        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)

        return Response(success_response(
            message=f'Compte de {user.email} invalidé et déconnecté.'
        ))
