"""Notifier webhook : POST JSON vers une URL configurable."""
import httpx

from app.core.logging import get_logger
from app.notifications.base import Notification, Notifier

logger = get_logger(__name__)


class WebhookNotifier(Notifier):
    def send(self, notification: Notification, config: dict) -> bool:
        url = config.get("url")
        if not url:
            logger.warning("WebhookNotifier: missing 'url' in channel config")
            return False
        payload = {
            "status": notification.status,
            "host": notification.host_name,
            "check": notification.check_name,
            "subject": notification.subject,
            "message": notification.body,
        }
        try:
            resp = httpx.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Webhook alert sent to %s (%s)", url, resp.status_code)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("WebhookNotifier failed: %s", exc)
            return False
