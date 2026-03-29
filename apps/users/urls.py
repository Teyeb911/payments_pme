from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, LogoutView,
    MeView, ChangePasswordView,
    UserListView, UserDetailView,
)

app_name = 'auth'

urlpatterns = [
    # Auth
    path('register/',        RegisterView.as_view(),       name='register'),
    path('login/',           LoginView.as_view(),          name='login'),
    path('logout/',          LogoutView.as_view(),         name='logout'),
    path('token/refresh/',   TokenRefreshView.as_view(),   name='token-refresh'),

    # Profile
    path('me/',              MeView.as_view(),             name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Admin
    path('users/',           UserListView.as_view(),       name='users-list'),
    path('users/<int:pk>/',  UserDetailView.as_view(),     name='users-detail'),
]
