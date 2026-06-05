import logging

import httpx

from src.notifications.base import NotificationChannel

logger = logging.getLogger(__name__)


class WebhookChannel(NotificationChannel):
    def send(self, subject: str, body: str) -> bool:
        url = self.config.get("url")
        if not url:
            logger.error("WebhookChannel: no 'url' key in config")
            return False

        # Basic SSRF guard: only allow https scheme
        if not url.startswith("https://"):
            logger.error("WebhookChannel: URL must use https, got: %s", url)
            return False

        response = httpx.post(
            url,
            json={"subject": subject, "body": body},
            timeout=10,
        )
        response.raise_for_status()
        logger.info("Webhook sent to %s (status %s)", url, response.status_code)
        return True
