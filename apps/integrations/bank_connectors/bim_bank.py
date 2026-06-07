from datetime import datetime, timedelta
from typing import List, Dict
from .base import BankConnectorBase


class BimBankConnector(BankConnectorBase):
    """Intégration API BimBank."""

    bank_name = 'BimBank'
    api_base = 'https://api.bimbank.mr/v1'

    def __init__(self, api_token: str):
        self.api_token = api_token

    def authenticate(self, credentials: dict) -> bool:
        if self.use_mock:
            return True
        return True

    def get_mock_data(self, account_id: str) -> List[Dict]:
        """Données de test BimBank."""
        from django.utils import timezone
        now = timezone.now()
        return [
            {
                'reference': f'BIMBANK-{account_id}-001',
                'montant': 75000.00,
                'type_transaction': 'credit',
                'description': 'Paiement facture client',
                'date': now - timedelta(days=8),
                'statut': 'completed',
            },
            {
                'reference': f'BIMBANK-{account_id}-002',
                'montant': 22000.00,
                'type_transaction': 'debit',
                'description': 'Paiement fournisseur',
                'date': now - timedelta(days=6),
                'statut': 'completed',
            },
        ]

    def fetch_transactions(
        self, account_id: str, from_date: datetime
    ) -> List[Dict]:
        if self.use_mock:
            return self.get_mock_data(account_id)
        return []

    def verify_webhook(self, payload: dict, signature: str) -> bool:
        return True
