"""Envoi des notifications push via Firebase Cloud Messaging.

Configuration (une seule des deux variables) :
  FIREBASE_CREDENTIALS       chemin vers le JSON du compte de service
  FIREBASE_CREDENTIALS_JSON  contenu du JSON (pratique sur Render)
Sans configuration, les envois sont ignorés sans erreur : un virement ne doit
jamais échouer à cause d'une notification.
"""
import json
import logging

from decouple import config

logger = logging.getLogger(__name__)
_app = None
_disabled = False


def _get_app():
    global _app, _disabled
    if _app is not None or _disabled:
        return _app
    try:
        import firebase_admin
        from firebase_admin import credentials

        raw = config('FIREBASE_CREDENTIALS_JSON', default='')
        path = config('FIREBASE_CREDENTIALS', default='')
        if raw:
            cred = credentials.Certificate(json.loads(raw))
        elif path:
            cred = credentials.Certificate(path)
        else:
            logger.info('Firebase non configuré : notifications push désactivées.')
            _disabled = True
            return None
        _app = firebase_admin.initialize_app(cred)
    except Exception:  # noqa: BLE001
        logger.exception('Initialisation Firebase impossible')
        _disabled = True
    return _app


def send_to_user(user, title, body, data=None):
    """Envoie une notification à tous les appareils de l'utilisateur.
    Retourne le nombre d'envois réussis ; supprime les jetons invalides."""
    from .models import DeviceToken

    app = _get_app()
    if app is None:
        return 0
    tokens = list(DeviceToken.objects.filter(user=user).values_list('token', flat=True))
    if not tokens:
        return 0

    from firebase_admin import messaging

    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                channel_id='transfers', sound='default'
            ),
        ),
    )
    try:
        resp = messaging.send_each_for_multicast(message, app=app)
    except Exception:  # noqa: BLE001
        logger.exception('Envoi FCM échoué')
        return 0

    dead = [
        tokens[i]
        for i, r in enumerate(resp.responses)
        if not r.success and r.exception is not None
        and getattr(r.exception, 'code', '') in ('NOT_FOUND', 'UNREGISTERED', 'INVALID_ARGUMENT')
    ]
    if dead:
        DeviceToken.objects.filter(token__in=dead).delete()
    return resp.success_count


def notify_transfer(transaction):
    """Notifie le destinataire (argent reçu) et l'expéditeur (confirmation)."""
    try:
        exp = transaction.wallet_expediteur.commercant
        rec = transaction.wallet_recepteur.commercant
        montant = f'{transaction.montant:,.0f}'.replace(',', ' ')
        data = {
            'type': 'transfer',
            'transaction_id': transaction.id,
            'reference': transaction.reference,
        }
        send_to_user(
            rec,
            'Paiement reçu 💰',
            f'Vous avez reçu {montant} MRU de {exp.nom or exp.telephone}.',
            data,
        )
        send_to_user(
            exp,
            'Transfert envoyé ✅',
            f'{montant} MRU envoyés à {rec.nom or rec.telephone}.',
            data,
        )
    except Exception:  # noqa: BLE001
        logger.exception('Notification de transfert impossible')
