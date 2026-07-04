from app.models.enums import ChannelType
from app.notifications.base import Notifier
from app.notifications.email_notifier import EmailNotifier
from app.notifications.slack_notifier import SlackNotifier
from app.notifications.telegram_notifier import TelegramNotifier
from app.notifications.teams_notifier import TeamsNotifier
from app.notifications.discord_notifier import DiscordNotifier
from app.notifications.sms_notifier import SmsNotifier
from app.notifications.script_notifier import ScriptNotifier
from app.notifications.webhook_notifier import WebhookNotifier

NOTIFIERS: dict[str, Notifier] = {
    ChannelType.EMAIL.value: EmailNotifier(),
    ChannelType.WEBHOOK.value: WebhookNotifier(),
    ChannelType.SLACK.value: SlackNotifier(),
    ChannelType.TELEGRAM.value: TelegramNotifier(),
    ChannelType.TEAMS.value: TeamsNotifier(),
    ChannelType.DISCORD.value: DiscordNotifier(),
    ChannelType.SMS.value: SmsNotifier(),
    ChannelType.SCRIPT.value: ScriptNotifier(),
}


def get_notifier(channel_type: str) -> Notifier | None:
    return NOTIFIERS.get(channel_type)
