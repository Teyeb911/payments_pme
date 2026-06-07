from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict
from django.conf import settings


class BankConnectorBase(ABC):
    """Interface abstraite pour tous les connecteurs bancaires."""

    bank_name: str = ''
    requires_api_key: bool = True
    use_mock = getattr(settings, 'BANK_SYNC_MODE', 'mock') == 'mock'

    @abstractmethod
    def authenticate(self, credentials: dict) -> bool:
        """Valider l'authentification."""
        pass

    @abstractmethod
    def fetch_transactions(
        self, account_id: str, from_date: datetime
    ) -> List[Dict]:
        """
        Récupérer les transactions depuis la banque.
        Retourne une liste de dicts avec:
        - reference (str): ID unique de la banque
        - montant (float): montant positif
        - type_transaction (str): 'credit' ou 'debit'
        - description (str)
        - date (datetime)
        - statut (str): 'completed', 'pending', 'failed'
        """
        pass

    @abstractmethod
    def get_mock_data(self, account_id: str) -> List[Dict]:
        """Données de test pour le mode mock."""
        pass

    @abstractmethod
    def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Valider la signature d'un webhook bancaire."""
        pass
