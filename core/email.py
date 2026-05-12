import os
import logging

import requests

logger = logging.getLogger(__name__)

_API_KEY   = os.environ.get('SENDGRID_API_KEY', '')
_FROM      = 'trackpay.platform@gmail.com'
_FROM_NAME = 'TrackPay'
_URL       = 'https://api.sendgrid.com/v3/mail/send'


def send_email(to: str, subject: str, body: str) -> bool:
    api_key = os.environ.get('SENDGRID_API_KEY', '')
    if not api_key:
        logger.error('SENDGRID_API_KEY not configured')
        return False

    try:
        resp = requests.post(
            _URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type':  'application/json',
            },
            json={
                'personalizations': [{'to': [{'email': to}]}],
                'from':    {'email': _FROM, 'name': _FROM_NAME},
                'subject': subject,
                'content': [{'type': 'text/plain', 'value': body}],
            },
            timeout=10,
        )
        if resp.status_code not in (200, 202):
            logger.error('SendGrid error %s: %s', resp.status_code, resp.text)
            return False
        logger.info('Email sent to %s', to)
        return True
    except Exception as exc:
        logger.error('SendGrid error: %s', exc)
        return False
