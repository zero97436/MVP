"""Notifier SMS via la passerelle Twilio.

config_json : {"account_sid": "AC...", "auth_token": "...", "from": "+33...", "to": "+33..."}
"""
import httpx

from app.core.logging import get_logger
from app.notifications.base import Notification, Notifier

logger = get_logger(__name__)


class SmsNotifier(Notifier):
    def send(self, notification: Notification, config: dict) -> bool:
        sid = config.get("account_sid")
        token = config.get("auth_token")
        sender = config.get("from")
        to = config.get("to")
        if not all([sid, token, sender, to]):
            logger.warning("SmsNotifier: config incomplète (account_sid/auth_token/from/to)")
            return False
        body = (
            f"[{notification.status}] {notification.host_name}/{notification.check_name} "
            f"{notification.body or ''}"
        )[:320]
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        try:
            resp = httpx.post(
                url, auth=(sid, token),
                data={"From": sender, "To": to, "Body": body}, timeout=15,
            )
            resp.raise_for_status()
            logger.info("SMS alert sent (%s)", resp.status_code)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("SmsNotifier failed: %s", exc)
            return False
