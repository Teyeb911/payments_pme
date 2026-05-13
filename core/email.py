import logging

import requests
from decouple import config

logger = logging.getLogger(__name__)

_URL    = 'https://bmnext.pythonanywhere.com/senders/send-email'
_SENDER = {'name': 'TrackPay', 'color': '#1E88E5'}


def send_email(to: str, subject: str, body: str) -> bool:
    # Email Microservice (local + production)
    api_key    = config('EMAIL_MICROSERVICE_KEY', default='')
    gmail_user = config('EMAIL_HOST_USER', default='')
    gmail_pass = config('EMAIL_HOST_PASSWORD', default='')

    if not api_key:
        logger.error('EMAIL_MICROSERVICE_KEY not configured')
        return False

    payload = {
        'api_key': api_key,
        'to':      to,
        'subject': subject,
        'message': body,
        'sender':  _SENDER,
    }

    if gmail_user and gmail_pass:
        payload['custom_email'] = {
            'email_sender':       gmail_user,
            'email_app_password': gmail_pass,
        }

    try:
        resp = requests.post(_URL, json=payload, timeout=15)
        if resp.status_code == 200:
            logger.info('Email sent to %s', to)
            return True
        logger.error('Microservice error %s: %s', resp.status_code, resp.text)
        return False
    except Exception as exc:
        logger.error('Microservice error: %s', exc)
        return False


def send_email_async(to: str, subject: str, body: str) -> None:
    import threading
    threading.Thread(target=send_email, args=(to, subject, body), daemon=True).start()
