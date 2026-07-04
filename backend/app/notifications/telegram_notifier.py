"""Notifier Telegram : message via l'API Bot.

config_json attendu : {"bot_token": "123:ABC", "chat_id": "123456789"}
Créer un bot avec @BotFather, récupérer le token ; chat_id via @userinfobot.
"""
import httpx

from app.core.logging import get_logger
from app.notifications.base import Notification, Notifier

logger = get_logger(__name__)

EMOJI = {"OK": "🟢", "WARNING": "🟡", "CRITICAL": "🔴", "UNKNOWN": "⚪"}


class TelegramNotifier(Notifier):
    def send(self, notification: Notification, config: dict) -> bool:
        token = config.get("bot_token")
        chat_id = config.get("chat_id")
        if not token or not chat_id:
            logger.warning("TelegramNotifier: missing 'bot_token' or 'chat_id'")
            return False
        emoji = EMOJI.get(notification.status, "")
        text = (
            f"{emoji} <b>[{notification.status}]</b> {notification.host_name} / "
            f"{notification.check_name}\n{notification.body}"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            resp = httpx.post(
                url,
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Telegram alert sent (%s)", resp.status_code)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("TelegramNotifier failed: %s", exc)
            return False
