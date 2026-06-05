import logging
from dataclasses import dataclass

from src.notifications.base import NotificationChannel
from src.notifications.channels.email import EmailChannel
from src.notifications.channels.slack import SlackChannel
from src.notifications.channels.webhook import WebhookChannel

logger = logging.getLogger(__name__)

CHANNEL_REGISTRY: dict[str, type[NotificationChannel]] = {
    "email": EmailChannel,
    "slack": SlackChannel,
    "webhook": WebhookChannel,
}


@dataclass
class DispatchResult:
    channel_id: str
    channel_type: str
    success: bool
    error: str | None = None


class NotificationDispatcher:
    def dispatch(self, subject: str, body: str, channels: list) -> list[DispatchResult]:
        results = []
        for ch in channels:
            if not ch.is_active:
                continue
            channel_type = ch.type.value if hasattr(ch.type, "value") else ch.type
            channel_class = CHANNEL_REGISTRY.get(channel_type)
            if not channel_class:
                logger.warning("Unknown channel type: %s", channel_type)
                continue
            try:
                success = channel_class(ch.config).send(subject, body)
                results.append(DispatchResult(str(ch.id), channel_type, success))
            except Exception as e:
                logger.error("Channel %s (%s) failed: %s", ch.id, channel_type, e)
                results.append(DispatchResult(str(ch.id), channel_type, False, str(e)))
        return results
