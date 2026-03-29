from django.urls import path
from .views import (
    HistoriqueView,
    TransactionDetailView,
    TransfertInterneView,
    AnnulerTransactionView,
    DashboardView,
    AllTransactionsView,
)

app_name = 'transactions'

urlpatterns = [
    # Commerçant
    path('',                          HistoriqueView.as_view(),         name='historique'),
    path('<int:pk>/',                 TransactionDetailView.as_view(),  name='detail'),
    path('transfert/',                TransfertInterneView.as_view(),   name='transfert'),
    path('<int:pk>/annuler/',         AnnulerTransactionView.as_view(), name='annuler'),
    path('dashboard/',                DashboardView.as_view(),          name='dashboard'),

    # Admin
    path('admin/all/',                AllTransactionsView.as_view(),    name='admin-all'),
]
