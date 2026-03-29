from django.urls import path
from .views import MyWalletView, ChargerWalletView, AllWalletsView

app_name = 'wallets'

urlpatterns = [
    path('me/',      MyWalletView.as_view(),     name='my-wallet'),
    path('charger/', ChargerWalletView.as_view(), name='charger-wallet'),
    path('all/',     AllWalletsView.as_view(),    name='all-wallets'),   # admin
]
