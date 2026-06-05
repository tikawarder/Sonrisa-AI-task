import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment

from src.core.config import settings
from src.notifications.base import NotificationChannel

logger = logging.getLogger(__name__)

# autoescape=True prevents HTML injection from untrusted event content
_env = Environment(autoescape=True)
_EMAIL_TEMPLATE = _env.from_string(
    "<html><body>"
    "<h2>{{ subject }}</h2>"
    "<p>{{ body }}</p>"
    "<hr><small>Sent by Alert Notification System</small>"
    "</body></html>"
)


class EmailChannel(NotificationChannel):
    def send(self, subject: str, body: str) -> bool:
        recipient = self.config.get("email")
        if not recipient:
            logger.error("EmailChannel: no 'email' key in config")
            return False

        html = _EMAIL_TEMPLATE.render(subject=subject, body=body)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = recipient
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email sent to %s", recipient)
        return True
