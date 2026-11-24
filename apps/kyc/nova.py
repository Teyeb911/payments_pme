"""Client NovaKYC (microservice de vérification d'identité).

Configuration (.env) :
  NOVA_KYC_URL     URL du service (défaut : http://13.61.190.119:8000)
  NOVA_KYC_KEY     clé API envoyée dans l'en-tête Secure-Nova-Key
  NOVA_KYC_TENANT  identifiant du tenant (défaut : trackpay)

Tant que NOVA_KYC_KEY est vide, `is_available()` renvoie False et l'app
garde l'ancien parcours KYC : il suffit d'ajouter la clé et de redémarrer.
"""
import base64
import logging
import uuid

import requests
from decouple import config

logger = logging.getLogger(__name__)

LIVENESS_MIN = 0.60  # seuil documenté par NovaKYC


class NovaUnavailable(Exception):
    """Clé absente ou service injoignable."""


class NovaError(Exception):
    def __init__(self, status_code, detail):
        super().__init__(f'NovaKYC {status_code}: {detail}')
        self.status_code = status_code
        self.detail = detail


def _url():
    return config('NOVA_KYC_URL', default='http://13.61.190.119:8000').rstrip('/')


def _key():
    return config('NOVA_KYC_KEY', default='')


def tenant():
    return config('NOVA_KYC_TENANT', default='trackpay')


def is_available():
    return bool(_key())


def _post(path, payload, timeout=60):
    if not is_available():
        raise NovaUnavailable('NOVA_KYC_KEY non configurée')
    try:
        resp = requests.post(
            f'{_url()}{path}',
            json=payload,
            headers={'Secure-Nova-Key': _key()},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise NovaUnavailable(str(exc)) from exc
    if resp.status_code in (401, 403):
        logger.error('NovaKYC refuse la clé API (%s)', resp.status_code)
        raise NovaUnavailable('Clé NovaKYC refusée')
    if resp.status_code >= 400:
        try:
            detail = resp.json().get('detail', resp.text)
        except ValueError:
            detail = resp.text
        raise NovaError(resp.status_code, detail)
    return resp.json()


def b64(django_file):
    django_file.seek(0)
    return base64.b64encode(django_file.read()).decode()


def full_verification(document_b64, selfie_b64, face_b64=None, client_ip=''):
    """Parcours complet : document → visage + vivacité → risque → décision.
    Retourne un dict prêt pour l'app."""
    t = tenant()
    session_id = f'trackpay-{uuid.uuid4().hex[:12]}'

    doc = _post('/api/kyc/document/verify', {
        'document_image': document_b64, 'tenant_id': t,
    })
    face = _post('/api/kyc/face/verify', {
        'document_image': face_b64 or document_b64,
        'selfie_image': selfie_b64,
        'perform_liveness': True,
        'tenant_id': t,
    })
    try:
        risk = _post('/api/kyc/risk/score', {
            'tenant_id': t,
            'session_id': session_id,
            'data': {'device': 'mobile', 'ip': client_ip},
        })
    except NovaError:
        risk = {'risk_level': 'MEDIUM', 'risk_score': None, 'factors': []}

    liveness_score = float(face.get('liveness_score') or 0)
    decision = _post('/api/kyc/kyc/complete', {
        'tenant_id': t,
        'session_id': session_id,
        'document_data': {
            'valid': bool(doc.get('valid')),
            'issues': doc.get('issues') or [],
            'risk_level': risk.get('risk_level'),
        },
        'face_data': {
            'verified': bool(face.get('verified')),
            'similarity': float(face.get('similarity') or 0),
            'liveness_passed': liveness_score >= LIVENESS_MIN,
            'liveness_score': liveness_score,
        },
    })

    return {
        'kyc_passed': bool(decision.get('kyc_passed')),
        'status': decision.get('status', 'REJECTED'),
        'rejection_reasons': decision.get('rejection_reasons') or [],
        'similarity': float(face.get('similarity') or 0),
        'liveness_score': liveness_score,
        'document_valid': bool(doc.get('valid')),
        'document_issues': doc.get('issues') or [],
        'risk_level': risk.get('risk_level'),
        'session_id': session_id,
    }
