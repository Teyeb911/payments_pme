from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from apps.comptes.models import CompteExterne, TransactionExterne
from .models import BankSync, SyncLog
from .bank_connectors import CONNECTORS


class SyncError(Exception):
    pass


class SyncOrchestrator:
    """Orchestrateur central pour les syncs de comptes externes."""

    @staticmethod
    def get_connector(compte_externe: CompteExterne):
        """Récupérer le connecteur pour un compte."""
        bank_type = compte_externe.type_compte.lower()
        ConnectorClass = CONNECTORS.get(bank_type)

        if not ConnectorClass:
            raise SyncError(f'Bank type {bank_type} not supported')

        if not compte_externe.api_token:
            raise SyncError(f'No API token for {compte_externe.nom_banque}')

        return ConnectorClass(compte_externe.api_token)

    @staticmethod
    @transaction.atomic
    def sync_account(compte_externe: CompteExterne, days_back: int = 30):
        """Synchroniser les transactions d'un compte externe."""
        bank_sync, _ = BankSync.objects.get_or_create(
            compte_externe=compte_externe,
            defaults={'status': BankSync.Status.PENDING}
        )

        bank_sync.status = BankSync.Status.SYNCING
        bank_sync.save(update_fields=['status'])

        try:
            connector = SyncOrchestrator.get_connector(compte_externe)
            from_date = timezone.now() - timedelta(days=days_back)

            # Récupérer les transactions
            txs = connector.fetch_transactions(
                compte_externe.numero_compte,
                from_date=from_date,
            )

            SyncLog.objects.create(
                bank_sync=bank_sync,
                action=SyncLog.Action.FETCH,
                message=f'Récupéré {len(txs)} transactions',
                count=len(txs),
            )

            # Créer/mettre à jour les transactions
            created_count = 0
            updated_count = 0

            for tx_data in txs:
                tx_obj, created = TransactionExterne.objects.update_or_create(
                    reference=tx_data['reference'],
                    defaults={
                        'compte_externe': compte_externe,
                        'montant': tx_data['montant'],
                        'type_transaction': tx_data['type_transaction'],
                        'description': tx_data['description'],
                        'date': tx_data['date'],
                        'statut': tx_data['statut'],
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            SyncLog.objects.create(
                bank_sync=bank_sync,
                action=SyncLog.Action.CREATE,
                message=f'Créées {created_count} transactions, mises à jour {updated_count}',
                count=created_count + updated_count,
            )

            # Marquer succès
            bank_sync.status = BankSync.Status.SUCCESS
            bank_sync.last_sync_at = timezone.now()
            bank_sync.last_successful_sync_at = timezone.now()
            bank_sync.error_message = ''
            bank_sync.next_sync_at = timezone.now() + timedelta(hours=1)
            bank_sync.save()

            return {
                'status': 'success',
                'created': created_count,
                'updated': updated_count,
                'total': len(txs),
            }

        except Exception as e:
            error_msg = str(e)

            SyncLog.objects.create(
                bank_sync=bank_sync,
                action=SyncLog.Action.ERROR,
                message=error_msg,
            )

            bank_sync.status = BankSync.Status.FAILED
            bank_sync.last_sync_at = timezone.now()
            bank_sync.error_message = error_msg
            bank_sync.next_sync_at = timezone.now() + timedelta(minutes=15)
            bank_sync.save()

            raise SyncError(error_msg)

    @staticmethod
    def sync_all_active():
        """Synchroniser tous les comptes actifs."""
        comptes = CompteExterne.objects.filter(is_actif=True)
        results = {'total': 0, 'success': 0, 'failed': 0}

        for compte in comptes:
            results['total'] += 1
            try:
                SyncOrchestrator.sync_account(compte)
                results['success'] += 1
            except SyncError:
                results['failed'] += 1

        return results
