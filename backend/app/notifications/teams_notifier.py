"""Notifier Microsoft Teams : MessageCard via une Incoming Webhook.

config_json : {"webhook_url": "https://outlook.office.com/webhook/..."}
"""
import httpx

from app.core.logging import get_logger
from app.notifications.base import Notification, Notifier

logger = get_logger(__name__)

COLOR = {"OK": "2EB67D", "WARNING": "F59E0B", "CRITICAL": "EF4444", "UNKNOWN": "64748B"}


class TeamsNotifier(Notifier):
    def send(self, notification: Notification, config: dict) -> bool:
        url = config.get("webhook_url") or config.get("url")
        if not url:
            logger.warning("TeamsNotifier: missing 'webhook_url'")
            return False
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": COLOR.get(notification.status, "64748B"),
            "summary": notification.subject,
            "title": f"[{notification.status}] {notification.host_name} / {notification.check_name}",
            "text": notification.body or "",
        }
        try:
            resp = httpx.post(url, json=card, timeout=10)
            resp.raise_for_status()
            logger.info("Teams alert sent (%s)", resp.status_code)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("TeamsNotifier failed: %s", exc)
            return False
