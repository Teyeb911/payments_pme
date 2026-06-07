from celery import shared_task
from django.utils import timezone

from apps.comptes.models import CompteExterne
from .services import SyncOrchestrator, SyncError


@shared_task
def sync_account_task(compte_externe_id: int, days_back: int = 30):
    """Syncer un compte externe de manière asynchrone."""
    try:
        compte = CompteExterne.objects.get(id=compte_externe_id)
        result = SyncOrchestrator.sync_account(compte, days_back=days_back)
        return {
            'status': 'success',
            'compte_id': compte_externe_id,
            'result': result,
        }
    except CompteExterne.DoesNotExist:
        return {'status': 'error', 'message': 'Compte not found'}
    except SyncError as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def sync_all_accounts_task():
    """Syncer tous les comptes actifs (job périodique)."""
    result = SyncOrchestrator.sync_all_active()
    return {
        'timestamp': str(timezone.now()),
        'result': result,
    }


@shared_task
def cleanup_old_sync_logs(days: int = 90):
    """Supprimer les vieux logs de sync (> N jours)."""
    from .models import SyncLog
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=days)
    deleted_count, _ = SyncLog.objects.filter(created_at__lt=cutoff).delete()
    return {'deleted': deleted_count}
