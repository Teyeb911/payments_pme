import os
import smtplib
import threading
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    gmail_user = os.environ.get('EMAIL_HOST_USER', '')
    gmail_pass = os.environ.get('EMAIL_HOST_PASSWORD', '')

    if not gmail_user or not gmail_pass:
        logger.error('EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not configured')
        return False

    def _send():
        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From']    = f'TrackPay <{gmail_user}>'
            msg['To']      = to
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as s:
                s.starttls()
                s.login(gmail_user, gmail_pass)
                s.send_message(msg)
            logger.info('Email sent to %s', to)
        except Exception as exc:
            logger.error('Gmail SMTP error: %s', exc)

    threading.Thread(target=_send, daemon=True).start()
    return True
