from .base import BankConnectorBase
from .bankili import BankiliConnector
from .sedad import SedadConnector
from .masrivi import MasriviConnector
from .bim_bank import BimBankConnector
from .paypal import PayPalConnector

__all__ = [
    'BankConnectorBase',
    'BankiliConnector',
    'SedadConnector',
    'MasriviConnector',
    'BimBankConnector',
    'PayPalConnector',
]

CONNECTORS = {
    'bankili': BankiliConnector,
    'sedad': SedadConnector,
    'masrivi': MasriviConnector,
    'bim_bank': BimBankConnector,
    'paypal': PayPalConnector,
}
