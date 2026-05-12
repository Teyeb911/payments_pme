import threading
import logging

import requests
from decouple import config
from django.core.mail import send_mail as django_send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

_SENDGRID_URL  = 'https://api.sendgrid.com/v3/mail/send'
_FROM_EMAIL    = 'trackpay.platform@gmail.com'
_FROM_NAME     = 'TrackPay'


def send_email(to: str, subject: str, body: str) -> bool:
    api_key = config('SENDGRID_API_KEY', default='')

    if api_key and not settings.DEBUG:
        # Production (Render) — SendGrid HTTPS API
        def _send():
            try:
                resp = requests.post(
                    _SENDGRID_URL,
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type':  'application/json',
                    },
                    json={
                        'personalizations': [{'to': [{'email': to}]}],
                        'from':    {'email': _FROM_EMAIL, 'name': _FROM_NAME},
                        'subject': subject,
                        'content': [{'type': 'text/plain', 'value': body}],
                    },
                    timeout=15,
                )
                if resp.status_code not in (200, 202):
                    logger.error('SendGrid error %s: %s', resp.status_code, resp.text)
                else:
                    logger.info('Email sent via SendGrid to %s', to)
            except Exception as exc:
                logger.error('SendGrid error: %s', exc)

        threading.Thread(target=_send, daemon=True).start()
        return True

    else:
        # Local — Django SMTP
        try:
            django_send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to],
                fail_silently=False,
            )
            logger.info('Email sent via SMTP to %s', to)
            return True
        except Exception as exc:
            logger.error('SMTP error: %s', exc)
            return False
