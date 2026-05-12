import logging
import smtplib
from email.mime.text import MIMEText

import requests
from decouple import config

logger = logging.getLogger(__name__)

_MICROSERVICE_URL = 'https://bmnext.pythonanywhere.com/senders/send-email'
_SENDER           = {'name': 'TrackPay', 'logo': None, 'color': '#1E88E5'}


def _send_via_microservice(api_key, to, subject, body):
    resp = requests.post(
        _MICROSERVICE_URL,
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
        logger.info('Email sent via microservice to %s', to)
        return True
    logger.error('Microservice error %s: %s', resp.status_code, resp.text)
    return False


def _send_via_smtp(to, subject, body):
    gmail_user = config('EMAIL_HOST_USER', default='')
    gmail_pass = config('EMAIL_HOST_PASSWORD', default='')
    if not gmail_user or not gmail_pass:
        logger.error('SMTP credentials not configured')
        return False
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From']    = f'TrackPay <{gmail_user}>'
    msg['To']      = to
    with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as s:
        s.starttls()
        s.login(gmail_user, gmail_pass)
        s.send_message(msg)
    logger.info('Email sent via SMTP to %s', to)
    return True


def send_email(to: str, subject: str, body: str) -> bool:
    is_debug  = config('DEBUG', default=False, cast=bool)
    api_key   = config('EMAIL_MICROSERVICE_KEY', default='')

    if is_debug:
        # Local — console (visible dans le terminal)
        from django.core.mail import send_mail
        from django.conf import settings
        try:
            send_mail(subject=subject, message=body,
                      from_email=settings.DEFAULT_FROM_EMAIL,
                      recipient_list=[to], fail_silently=False)
            return True
        except Exception as exc:
            logger.error('Console email error: %s', exc)
            return False

    # Production — microservice d'abord, SMTP en fallback
    try:
        if api_key and _send_via_microservice(api_key, to, subject, body):
            return True
    except Exception as exc:
        logger.error('Microservice failed: %s', exc)

    try:
        return _send_via_smtp(to, subject, body)
    except Exception as exc:
        logger.error('SMTP fallback failed: %s', exc)
        return False
