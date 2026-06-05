import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.core.config import settings
from src.notifications.base import NotificationChannel

logger = logging.getLogger(__name__)


class SlackChannel(NotificationChannel):
    def __init__(self, config: dict):
        super().__init__(config)
        self._client = WebClient(token=settings.SLACK_BOT_TOKEN)

    def send(self, subject: str, body: str) -> bool:
        channel = self.config.get("channel")
        if not channel:
            logger.error("SlackChannel: no 'channel' key in config")
            return False

        try:
            self._client.chat_postMessage(
                channel=channel,
                text=f"*{subject}*\n{body}",
            )
            logger.info("Slack message sent to %s", channel)
            return True
        except SlackApiError as e:
            logger.error("Slack API error: %s", e.response["error"])
            return False
