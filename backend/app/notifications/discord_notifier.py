"""Notifier Discord : message via une Webhook de salon.

config_json : {"webhook_url": "https://discord.com/api/webhooks/..."}
"""
import httpx

from app.core.logging import get_logger
from app.notifications.base import Notification, Notifier

logger = get_logger(__name__)

EMOJI = {"OK": "🟢", "WARNING": "🟡", "CRITICAL": "🔴", "UNKNOWN": "⚪"}


class DiscordNotifier(Notifier):
    def send(self, notification: Notification, config: dict) -> bool:
        url = config.get("webhook_url") or config.get("url")
        if not url:
            logger.warning("DiscordNotifier: missing 'webhook_url'")
            return False
        emoji = EMOJI.get(notification.status, "")
        content = (
            f"{emoji} **[{notification.status}]** {notification.host_name} / "
            f"{notification.check_name}\n{notification.body or ''}"
        )
        try:
            resp = httpx.post(url, json={"content": content[:1900]}, timeout=10)
            resp.raise_for_status()
            logger.info("Discord alert sent (%s)", resp.status_code)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("DiscordNotifier failed: %s", exc)
            return False
