from unittest.mock import MagicMock, patch

import pytest

from src.notifications.base import NotificationChannel
from src.notifications.channels.email import EmailChannel
from src.notifications.channels.slack import SlackChannel
from src.notifications.channels.webhook import WebhookChannel
from src.notifications.dispatcher import CHANNEL_REGISTRY, DispatchResult, NotificationDispatcher


def make_channel_model(type_val: str, config: dict, is_active: bool = True):
    ch = MagicMock()
    ch.id = "channel-001"
    ch.type.value = type_val
    ch.config = config
    ch.is_active = is_active
    return ch


# --- ABC ---

def test_notification_channel_is_abstract():
    with pytest.raises(TypeError):
        NotificationChannel({})


# --- CHANNEL_REGISTRY ---

def test_registry_contains_all_channel_types():
    assert "email" in CHANNEL_REGISTRY
    assert "slack" in CHANNEL_REGISTRY
    assert "webhook" in CHANNEL_REGISTRY


# --- EmailChannel ---

@patch("src.notifications.channels.email.smtplib.SMTP")
def test_email_channel_sends(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    ch = EmailChannel({"email": "user@example.com"})
    result = ch.send("Alert: Earthquake", "A 6.5 quake hit Turkey.")

    assert result is True
    mock_server.send_message.assert_called_once()


def test_email_channel_missing_config_returns_false():
    ch = EmailChannel({})
    assert ch.send("Subject", "Body") is False


# --- SlackChannel ---

@patch("src.notifications.channels.slack.WebClient")
def test_slack_channel_sends(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    ch = SlackChannel({"channel": "#alerts"})
    result = ch.send("Alert: Earthquake", "A 6.5 quake hit Turkey.")

    assert result is True
    mock_client.chat_postMessage.assert_called_once_with(
        channel="#alerts",
        text="*Alert: Earthquake*\nA 6.5 quake hit Turkey.",
    )


def test_slack_channel_missing_config_returns_false():
    ch = SlackChannel({})
    assert ch.send("Subject", "Body") is False


# --- WebhookChannel ---

@patch("src.notifications.channels.webhook.httpx.post")
def test_webhook_channel_sends(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = MagicMock()

    ch = WebhookChannel({"url": "https://hook.example.com/notify"})
    result = ch.send("Alert", "Body text")

    assert result is True
    mock_post.assert_called_once_with(
        "https://hook.example.com/notify",
        json={"subject": "Alert", "body": "Body text"},
        timeout=10,
    )


def test_webhook_channel_missing_config_returns_false():
    ch = WebhookChannel({})
    assert ch.send("Subject", "Body") is False


# --- NotificationDispatcher ---

@patch("src.notifications.channels.email.smtplib.SMTP")
def test_dispatcher_dispatches_active_channels(mock_smtp):
    mock_smtp.return_value.__enter__.return_value = MagicMock()
    dispatcher = NotificationDispatcher()
    channels = [make_channel_model("email", {"email": "user@example.com"})]

    results = dispatcher.dispatch("Alert", "Body", channels)

    assert len(results) == 1
    assert results[0].success is True


def test_dispatcher_skips_inactive_channels():
    dispatcher = NotificationDispatcher()
    channels = [make_channel_model("email", {"email": "x@y.com"}, is_active=False)]

    results = dispatcher.dispatch("Alert", "Body", channels)
    assert results == []


def test_dispatcher_handles_channel_exception():
    dispatcher = NotificationDispatcher()
    channels = [make_channel_model("webhook", {"url": "https://broken.example.com"})]

    with patch("src.notifications.channels.webhook.httpx.post", side_effect=Exception("timeout")):
        results = dispatcher.dispatch("Alert", "Body", channels)

    assert results[0].success is False
    assert "timeout" in results[0].error


def test_dispatcher_unknown_channel_type_skipped():
    dispatcher = NotificationDispatcher()
    channels = [make_channel_model("telegram", {"chat_id": "123"})]

    results = dispatcher.dispatch("Alert", "Body", channels)
    assert results == []
