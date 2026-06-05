from unittest.mock import MagicMock, patch
import uuid
from datetime import datetime, timezone

import pytest

from src.sources.base import Event
from src.matching.matcher import AlertConfig, AlertMatch
from src.workers.tasks import _hash, fetch_and_dispatch


def make_event(title="Earthquake hits Turkey"):
    return Event(
        title=title,
        description="A 6.5 magnitude quake struck.",
        url="https://bbc.com/news/1",
        published_at=datetime(2026, 6, 5, 10, 0, tzinfo=timezone.utc),
        source="BBC News",
    )


def test_hash_is_deterministic():
    aid = uuid.uuid4()
    h1 = _hash(aid, "https://example.com/1", "2026-06-05")
    h2 = _hash(aid, "https://example.com/1", "2026-06-05")
    assert h1 == h2


def test_hash_differs_for_different_urls():
    aid = uuid.uuid4()
    assert _hash(aid, "https://a.com", "2026") != _hash(aid, "https://b.com", "2026")


@patch("src.workers.tasks.SessionLocal")
@patch("src.workers.tasks.RSSSource")
@patch("src.workers.tasks.AlertMatcher")
@patch("src.workers.tasks.NotificationDispatcher")
def test_fetch_and_dispatch_no_alerts(mock_dispatcher, mock_matcher, mock_rss, mock_session):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_db.query.return_value.filter.return_value.all.return_value = []

    result = fetch_and_dispatch()

    assert result == {"matched": 0, "sent": 0}
    mock_db.commit.assert_not_called()  # early return before any DB writes


@patch("src.workers.tasks.SessionLocal")
@patch("src.workers.tasks.RSSSource")
@patch("src.workers.tasks.AlertMatcher")
@patch("src.workers.tasks.NotificationDispatcher")
def test_fetch_and_dispatch_skips_duplicate(mock_dispatcher_cls, mock_matcher_cls, mock_rss_cls, mock_session):
    alert_id = uuid.uuid4()
    event = make_event()

    mock_db = MagicMock()
    mock_session.return_value = mock_db

    mock_alert = MagicMock()
    mock_alert.id = alert_id
    mock_alert.is_active = True
    mock_alert.keywords = ["earthquake"]
    mock_alert.topic = None
    mock_alert.use_llm = False
    mock_alert.threshold = 0.7

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_alert]
    mock_rss_cls.return_value.fetch.return_value = [event]

    match = AlertMatch(alert_id=alert_id, event=event, matched_by="keyword")
    mock_matcher_cls.return_value.match.return_value = [match]

    # Simulate hash already in DB (duplicate)
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

    result = fetch_and_dispatch()

    assert result["matched"] == 0
    mock_dispatcher_cls.return_value.dispatch.assert_not_called()


@patch("src.workers.tasks.SessionLocal")
@patch("src.workers.tasks.RSSSource")
@patch("src.workers.tasks.AlertMatcher")
@patch("src.workers.tasks.NotificationDispatcher")
def test_fetch_and_dispatch_rollback_on_error(mock_dispatcher_cls, mock_matcher_cls, mock_rss_cls, mock_session):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_rss_cls.return_value.fetch.side_effect = Exception("network error")

    with pytest.raises(Exception, match="network error"):
        fetch_and_dispatch()

    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()
