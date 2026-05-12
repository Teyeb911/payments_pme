import os
import logging

import resend

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get('RESEND_API_KEY', '')

FROM_EMAIL = 'TrackPay <noreply@trackpay.ma>'


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email via Resend. Returns True on success."""
    if not resend.api_key:
        logger.error('RESEND_API_KEY not configured')
        return False
    try:
        resend.Emails.send({
            'from':    FROM_EMAIL,
            'to':      [to],
            'subject': subject,
            'text':    body,
        })
        return True
    except Exception as exc:
        logger.error('Resend error: %s', exc)
        return False
