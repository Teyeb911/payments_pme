import requests
from datetime import datetime, timedelta
from typing import List, Dict
from .base import BankConnectorBase


class BankiliConnector(BankConnectorBase):
    """Intégration API Bankili."""

    bank_name = 'Bankili'
    api_base = 'https://api.bankili.mr/v1'

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
        })

    def authenticate(self, credentials: dict) -> bool:
        """Valider le token Bankili."""
        if self.use_mock:
            return True
        try:
            res = self.session.post(
                f'{self.api_base}/auth/verify',
                json={'token': self.api_token},
                timeout=5,
            )
            return res.status_code == 200
        except Exception:
            return False

    def get_mock_data(self, account_id: str) -> List[Dict]:
        """Données de test Bankili."""
        from django.utils import timezone
        now = timezone.now()
        return [
            {
                'reference': f'BANKILI-{account_id}-001',
                'montant': 85000.00,
                'type_transaction': 'credit',
                'description': 'Paiement client - Commande #1001',
                'date': now - timedelta(days=5),
                'statut': 'completed',
            },
            {
                'reference': f'BANKILI-{account_id}-002',
                'montant': 12000.00,
                'type_transaction': 'debit',
                'description': 'Frais de transaction',
                'date': now - timedelta(days=4),
                'statut': 'completed',
            },
            {
                'reference': f'BANKILI-{account_id}-003',
                'montant': 150000.00,
                'type_transaction': 'credit',
                'description': 'Vente produits électroniques',
                'date': now - timedelta(days=3),
                'statut': 'completed',
            },
            {
                'reference': f'BANKILI-{account_id}-004',
                'montant': 25000.00,
                'type_transaction': 'debit',
                'description': 'Retrait espèces',
                'date': now - timedelta(days=2),
                'statut': 'completed',
            },
            {
                'reference': f'BANKILI-{account_id}-005',
                'montant': 95000.00,
                'type_transaction': 'credit',
                'description': 'Paiement fournisseur',
                'date': now - timedelta(days=1),
                'statut': 'completed',
            },
        ]

    def fetch_transactions(
        self, account_id: str, from_date: datetime
    ) -> List[Dict]:
        """Récupérer les transactions depuis Bankili."""
        if self.use_mock:
            return self.get_mock_data(account_id)

        try:
            res = self.session.get(
                f'{self.api_base}/accounts/{account_id}/transactions',
                params={'from_date': from_date.isoformat()},
                timeout=10,
            )
            res.raise_for_status()

            transactions = []
            for tx in res.json().get('data', []):
                transactions.append({
                    'reference': tx['id'],
                    'montant': abs(float(tx['amount'])),
                    'type_transaction': 'credit' if float(tx['amount']) > 0 else 'debit',
                    'description': tx.get('description', 'Bankili transaction'),
                    'date': datetime.fromisoformat(tx['timestamp']),
                    'statut': 'completed' if tx.get('status') == 'success' else 'pending',
                })
            return transactions
        except Exception as e:
            raise Exception(f'Bankili fetch error: {str(e)}')

    def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Valider la signature du webhook Bankili."""
        if self.use_mock:
            return True

        import hmac
        import hashlib
        import json

        try:
            expected = hmac.new(
                self.api_token.encode(),
                json.dumps(payload, separators=(',', ':')).encode(),
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            return False
