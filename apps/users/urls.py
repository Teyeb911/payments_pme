from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, LogoutView,
    MeView, ChangePasswordView,
    UserListView, UserDetailView,CheckEmailView,
    SendVerificationCodeView,VerifyCodeView,ForgotPasswordView,
VerifyResetCodeView, ResetPasswordView,SSOLoginView
)

app_name = 'auth'

urlpatterns = [
    # Auth
    path('register/',        RegisterView.as_view(),       name='register'),
    path('login/',           LoginView.as_view(),          name='login'),
    path('logout/',          LogoutView.as_view(),         name='logout'),
    path('token/refresh/',   TokenRefreshView.as_view(),   name='token-refresh'),
    path('check-email/', CheckEmailView.as_view(), name='check-email'),
    path('sso-login/', SSOLoginView.as_view(), name='sso-login'),    path('forgot-password/',        ForgotPasswordView.as_view(),    name='forgot-password'),
    path('verify-reset-code/',      VerifyResetCodeView.as_view(),   name='verify-reset-code'),
    path('reset-password/',         ResetPasswordView.as_view(),     name='reset-password'),

    # Profile
    path('me/',              MeView.as_view(),             name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('send-verification/', SendVerificationCodeView.as_view(), name='send-verification'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    # Admin
    path('users/',           UserListView.as_view(),       name='users-list'),
    path('users/<int:pk>/',  UserDetailView.as_view(),     name='users-detail'),
]
