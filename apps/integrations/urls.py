from django.urls import path
from .views import (
    SyncAccountView,
    BankSyncStatusView,
    SyncLogListView,
    ImportTransactionsView,
)

app_name = 'integrations'

urlpatterns = [
    path('comptes/<int:pk>/sync/', SyncAccountView.as_view(), name='sync'),
    path('comptes/<int:pk>/sync-status/', BankSyncStatusView.as_view(), name='sync_status'),
    path('comptes/<int:pk>/sync-logs/', SyncLogListView.as_view(), name='sync_logs'),
    path('comptes/<int:pk>/import/', ImportTransactionsView.as_view(), name='import'),
]
