import os
import smtplib
import threading
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

_GMAIL_USER = os.environ.get('EMAIL_HOST_USER', '')
_GMAIL_PASS = os.environ.get('EMAIL_HOST_PASSWORD', '')


def send_email(to: str, subject: str, body: str) -> bool:
    """Send email via Gmail SMTP in a background thread (non-blocking)."""
    if not _GMAIL_USER or not _GMAIL_PASS:
        logger.error('EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not configured')
        return False

    def _send():
        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From']    = f'TrackPay <{_GMAIL_USER}>'
            msg['To']      = to
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as s:
                s.starttls()
                s.login(_GMAIL_USER, _GMAIL_PASS)
                s.send_message(msg)
            logger.info('Email sent to %s', to)
        except Exception as exc:
            logger.error('Gmail SMTP error: %s', exc)

    threading.Thread(target=_send, daemon=True).start()
    return True
