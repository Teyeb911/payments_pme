from datetime import datetime, timedelta
from typing import List, Dict
from .base import BankConnectorBase


class MasriviConnector(BankConnectorBase):
    """Intégration API Masrivi."""

    bank_name = 'Masrivi'
    api_base = 'https://api.masrivi.mr/v1'

    def __init__(self, api_token: str):
        self.api_token = api_token

    def authenticate(self, credentials: dict) -> bool:
        if self.use_mock:
            return True
        return True

    def get_mock_data(self, account_id: str) -> List[Dict]:
        """Données de test Masrivi."""
        from django.utils import timezone
        now = timezone.now()
        return [
            {
                'reference': f'MASRIVI-{account_id}-001',
                'montant': 55000.00,
                'type_transaction': 'credit',
                'description': 'Vente marchandise',
                'date': now - timedelta(days=7),
                'statut': 'completed',
            },
            {
                'reference': f'MASRIVI-{account_id}-002',
                'montant': 18000.00,
                'type_transaction': 'debit',
                'description': 'Achat stock',
                'date': now - timedelta(days=4),
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
