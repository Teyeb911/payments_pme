"""Envoi des emails TrackPay (codes de vérification, réinitialisation…).

1. Brevo (API HTTP, BREVO_API_KEY) — requis sur Render gratuit qui bloque le SMTP.
2. SMTP Gmail via Django (EMAIL_HOST_USER + EMAIL_HOST_PASSWORD,
   où le mot de passe est un « mot de passe d'application » Google de 16 lettres).
3. Secours : l'ancien microservice HTTP, seulement si EMAIL_MICROSERVICE_KEY est défini.

Le texte brut des vues est conservé ; une version HTML aux couleurs TrackPay
est générée automatiquement (le code à 6 chiffres est mis en avant).
"""
import html
import logging
import re
import threading

import requests
from decouple import config
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)

_MICROSERVICE_URL = 'https://bmnext.pythonanywhere.com/senders/send-email'
_SENDER = {'name': 'TrackPay', 'color': '#1E88E5'}


def _html(subject: str, body: str) -> str:
    text = html.escape(body)
    # Met en valeur le code à 6 chiffres s'il y en a un.
    text = re.sub(
        r'\b(\d{6})\b',
        r'<div style="font-size:32px;font-weight:800;letter-spacing:8px;'
        r'color:#2563EB;background:#EFF6FF;border-radius:12px;padding:16px;'
        r'text-align:center;margin:16px 0">\1</div>',
        text,
        count=1,
    )
    text = text.replace('\n', '<br>')
    return f"""<!doctype html><html><body style="margin:0;background:#F8FAFC;
font-family:Arial,Helvetica,sans-serif;color:#0F172A">
<div style="max-width:520px;margin:24px auto;background:#fff;border-radius:16px;
overflow:hidden;border:1px solid #E2E8F0">
<div style="background:#2563EB;color:#fff;padding:20px 24px;font-size:20px;
font-weight:700">TrackPay</div>
<div style="padding:24px;font-size:15px;line-height:1.6">
<h2 style="margin:0 0 12px;font-size:18px">{html.escape(subject)}</h2>{text}</div>
<div style="padding:16px 24px;color:#94A3B8;font-size:12px;border-top:1px solid #E2E8F0">
© TrackPay — email automatique, merci de ne pas répondre.</div></div></body></html>"""


def _send_smtp(to: str, subject: str, body: str) -> bool:
    user = settings.EMAIL_HOST_USER
    if not user or not settings.EMAIL_HOST_PASSWORD:
        logger.warning('SMTP non configuré (EMAIL_HOST_USER / EMAIL_HOST_PASSWORD)')
        return False
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=f'TrackPay <{user}>',  # Gmail impose l'adresse du compte
            to=[to],
        )
        msg.attach_alternative(_html(subject, body), 'text/html')
        msg.send(fail_silently=False)
        logger.info('Email envoyé (SMTP) à %s', to)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error('SMTP : échec d\'envoi à %s : %s', to, exc)
        return False


def _send_microservice(to: str, subject: str, body: str) -> bool:
    api_key = config('EMAIL_MICROSERVICE_KEY', default='')
    if not api_key:
        return False
    payload = {'api_key': api_key, 'to': to, 'subject': subject,
               'message': body, 'sender': _SENDER}
    try:
        resp = requests.post(_MICROSERVICE_URL, json=payload, timeout=15)
        if resp.status_code == 200:
            logger.info('Email envoyé (microservice) à %s', to)
            return True
        logger.error('Microservice email %s', resp.status_code)
    except Exception as exc:  # noqa: BLE001
        logger.error('Microservice email : %s', exc)
    return False


def _send_brevo(to: str, subject: str, body: str) -> bool:
    """API HTTP Brevo (port 443) : fonctionne sur Render, qui bloque le SMTP
    sur les instances gratuites. Expéditeur = BREVO_SENDER (adresse vérifiée
    dans Brevo), par défaut EMAIL_HOST_USER."""
    api_key = config('BREVO_API_KEY', default='')
    if not api_key:
        return False
    sender = config('BREVO_SENDER', default='') or settings.EMAIL_HOST_USER
    try:
        resp = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={'api-key': api_key, 'accept': 'application/json'},
            json={
                'sender': {'name': 'TrackPay', 'email': sender},
                'to': [{'email': to}],
                'subject': subject,
                'textContent': body,
                'htmlContent': _html(subject, body),
            },
            timeout=15,
        )
        if resp.status_code in (200, 201, 202):
            logger.info('Email envoyé (Brevo) à %s', to)
            return True
        logger.error('Brevo %s : %s', resp.status_code, resp.text[:300])
    except Exception as exc:  # noqa: BLE001
        logger.error('Brevo : %s', exc)
    return False


def send_email(to: str, subject: str, body: str) -> bool:
    # 1. Brevo (HTTP) si configuré — seule voie qui marche sur Render gratuit.
    if _send_brevo(to, subject, body):
        return True
    # 2. SMTP Gmail — marche en local et sur les hébergeurs qui l'autorisent.
    if _send_smtp(to, subject, body):
        return True
    if _send_microservice(to, subject, body):
        return True
    logger.error('Aucun moyen d\'envoyer l\'email à %s', to)
    return False


def send_email_async(to: str, subject: str, body: str) -> None:
    threading.Thread(target=send_email, args=(to, subject, body), daemon=True).start()
