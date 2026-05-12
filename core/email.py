import os
import threading
import logging

import requests

logger = logging.getLogger(__name__)

_API_KEY   = os.environ.get('SENDGRID_API_KEY', '')
_FROM      = 'trackpay.platform@gmail.com'
_FROM_NAME = 'TrackPay'
_URL       = 'https://api.sendgrid.com/v3/mail/send'


def send_email(to: str, subject: str, body: str) -> bool:
    """Send email via SendGrid HTTPS API in background thread."""
    if not _API_KEY:
        logger.error('SENDGRID_API_KEY not configured')
        return False

    def _send():
        try:
            resp = requests.post(
                _URL,
                headers={
                    'Authorization': f'Bearer {_API_KEY}',
                    'Content-Type':  'application/json',
                },
                json={
                    'personalizations': [{'to': [{'email': to}]}],
                    'from':    {'email': _FROM, 'name': _FROM_NAME},
                    'subject': subject,
                    'content': [{'type': 'text/plain', 'value': body}],
                },
                timeout=15,
            )
            if resp.status_code not in (200, 202):
                logger.error('SendGrid error %s: %s', resp.status_code, resp.text)
            else:
                logger.info('Email sent to %s', to)
        except Exception as exc:
            logger.error('SendGrid error: %s', exc)

    threading.Thread(target=_send, daemon=True).start()
    return True
