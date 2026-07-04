"""Notifier email via SMTP."""
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging import get_logger
from app.notifications.base import Notification, Notifier

logger = get_logger(__name__)


class EmailNotifier(Notifier):
    def send(self, notification: Notification, config: dict) -> bool:
        to_addr = config.get("to")
        if not to_addr:
            logger.warning("EmailNotifier: missing 'to' in channel config")
            return False
        if not settings.SMTP_HOST:
            logger.warning("EmailNotifier: SMTP_HOST not configured, skipping")
            return False

        msg = MIMEText(notification.body)
        msg["Subject"] = notification.subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_addr

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Email alert sent to %s", to_addr)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("EmailNotifier failed: %s", exc)
            return False
