from django.urls import path
from .views import (
    CompteListCreateView,
    CompteDetailView,
    PaiementsEntrantsView,
    TransactionExterneListCreateView,
    ToutesTransactionsExternesView,
    DashboardExternesView,
)

app_name = 'comptes'

urlpatterns = [
    path('',                                   CompteListCreateView.as_view(),          name='liste'),
    path('<int:pk>/',                          CompteDetailView.as_view(),              name='detail'),
    path('<int:pk>/paiements/',                PaiementsEntrantsView.as_view(),         name='paiements'),
    path('<int:pk>/transactions/',             TransactionExterneListCreateView.as_view(), name='transactions'),
    path('transactions/toutes/',               ToutesTransactionsExternesView.as_view(), name='toutes_transactions'),
    path('dashboard/',                         DashboardExternesView.as_view(),         name='dashboard'),
]
