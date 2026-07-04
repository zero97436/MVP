"""Notifier Slack : message via une Incoming Webhook.

config_json attendu : {"webhook_url": "https://hooks.slack.com/services/..."}
"""
import httpx

from app.core.logging import get_logger
from app.notifications.base import Notification, Notifier

logger = get_logger(__name__)

EMOJI = {"OK": ":large_green_circle:", "WARNING": ":large_yellow_circle:",
         "CRITICAL": ":red_circle:", "UNKNOWN": ":white_circle:"}


class SlackNotifier(Notifier):
    def send(self, notification: Notification, config: dict) -> bool:
        url = config.get("webhook_url") or config.get("url")
        if not url:
            logger.warning("SlackNotifier: missing 'webhook_url' in channel config")
            return False
        emoji = EMOJI.get(notification.status, "")
        text = (
            f"{emoji} *[{notification.status}]* {notification.host_name} / "
            f"{notification.check_name}\n{notification.body}"
        )
        try:
            resp = httpx.post(url, json={"text": text}, timeout=10)
            resp.raise_for_status()
            logger.info("Slack alert sent (%s)", resp.status_code)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("SlackNotifier failed: %s", exc)
            return False
