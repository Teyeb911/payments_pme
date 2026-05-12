import logging

import requests
from decouple import config

logger = logging.getLogger(__name__)

_URL        = 'https://bmnext.pythonanywhere.com/senders/send-email'
_SENDER     = {'name': 'TrackPay', 'logo': None, 'color': '#1E88E5'}


def send_email(to: str, subject: str, body: str) -> bool:
    api_key = config('EMAIL_MICROSERVICE_KEY', default='')

    if api_key and not config('DEBUG', default=False, cast=bool):
        # Production — Email Microservice (HTTPS, non bloqué par Render)
        try:
            resp = requests.post(
                _URL,
                json={
                    'api_key': api_key,
                    'to':      to,
                    'subject': subject,
                    'message': body,
                    'sender':  _SENDER,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info('Email sent to %s', to)
                return True
            logger.error('Email microservice error %s: %s', resp.status_code, resp.text)
            return False
        except Exception as exc:
            logger.error('Email microservice error: %s', exc)
            return False

    else:
        # Local — Django SMTP
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
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
