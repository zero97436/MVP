"""Fabrique de notifiers.

Community : e-mail + webhook. Les canaux avancés (Slack, Teams, Discord,
Telegram, SMS, script) sont fournis par le paquet Enterprise via le hook
`get_notifier` (app.core.extensions) — leur code n'est pas livré en Community.
"""
from app.models.enums import ChannelType
from app.notifications.base import Notifier
from app.notifications.email_notifier import EmailNotifier
from app.notifications.webhook_notifier import WebhookNotifier

NOTIFIERS: dict[str, Notifier] = {
    ChannelType.EMAIL.value: EmailNotifier(),
    ChannelType.WEBHOOK.value: WebhookNotifier(),
}


def get_notifier(channel_type: str) -> Notifier | None:
    notifier = NOTIFIERS.get(channel_type)
    if notifier is not None:
        return notifier
    # Canal avancé : fourni par le paquet Enterprise s'il est installé.
    from app.core import extensions

    return extensions.call("get_notifier", channel_type)
