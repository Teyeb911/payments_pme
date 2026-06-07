from datetime import datetime, timedelta
from typing import List, Dict
from .base import BankConnectorBase


class PayPalConnector(BankConnectorBase):
    """Intégration API PayPal."""

    bank_name = 'PayPal'
    api_base = 'https://api.paypal.com/v1'

    def __init__(self, api_token: str):
        self.api_token = api_token

    def authenticate(self, credentials: dict) -> bool:
        if self.use_mock:
            return True
        return True

    def get_mock_data(self, account_id: str) -> List[Dict]:
        """Données de test PayPal."""
        from django.utils import timezone
        now = timezone.now()
        return [
            {
                'reference': f'PAYPAL-{account_id}-001',
                'montant': 95000.00,
                'type_transaction': 'credit',
                'description': 'Paiement international reçu',
                'date': now - timedelta(days=9),
                'statut': 'completed',
            },
            {
                'reference': f'PAYPAL-{account_id}-002',
                'montant': 5000.00,
                'type_transaction': 'debit',
                'description': 'Frais PayPal',
                'date': now - timedelta(days=7),
                'statut': 'completed',
            },
            {
                'reference': f'PAYPAL-{account_id}-003',
                'montant': 35000.00,
                'type_transaction': 'credit',
                'description': 'Paiement client PayPal',
                'date': now - timedelta(days=2),
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
