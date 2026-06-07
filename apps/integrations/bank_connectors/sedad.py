from datetime import datetime, timedelta
from typing import List, Dict
from .base import BankConnectorBase


class SedadConnector(BankConnectorBase):
    """Intégration API Sedad."""

    bank_name = 'Sedad'
    api_base = 'https://api.sedad.mr/v1'

    def __init__(self, api_token: str):
        self.api_token = api_token

    def authenticate(self, credentials: dict) -> bool:
        if self.use_mock:
            return True
        return True

    def get_mock_data(self, account_id: str) -> List[Dict]:
        """Données de test Sedad."""
        from django.utils import timezone
        now = timezone.now()
        return [
            {
                'reference': f'SEDAD-{account_id}-001',
                'montant': 65000.00,
                'type_transaction': 'credit',
                'description': 'Paiement client - Service professionnel',
                'date': now - timedelta(days=6),
                'statut': 'completed',
            },
            {
                'reference': f'SEDAD-{account_id}-002',
                'montant': 8500.00,
                'type_transaction': 'debit',
                'description': 'Frais Sedad',
                'date': now - timedelta(days=5),
                'statut': 'completed',
            },
            {
                'reference': f'SEDAD-{account_id}-003',
                'montant': 120000.00,
                'type_transaction': 'credit',
                'description': 'Versement client',
                'date': now - timedelta(days=3),
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
