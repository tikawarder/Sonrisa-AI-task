import time
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.sources.base import Event, EventSource
from src.sources.rss import RSSSource

MOCK_FEED = {
    "feed": {"title": "BBC News"},
    "entries": [
        {
            "title": "Earthquake hits Turkey",
            "summary": "A 6.5 magnitude earthquake struck the region.",
            "link": "https://bbc.com/news/1",
            "published_parsed": time.struct_time((2026, 6, 5, 10, 0, 0, 0, 0, 0)),
        },
        {
            "title": "Flooding in Germany",
            "summary": "Heavy rain caused widespread flooding.",
            "link": "https://bbc.com/news/2",
            "published_parsed": time.struct_time((2026, 6, 5, 11, 0, 0, 0, 0, 0)),
        },
    ],
}

EMPTY_FEED = {"feed": {"title": "Empty Feed"}, "entries": []}


def test_event_source_is_abstract():
    with pytest.raises(TypeError):
        EventSource()


@patch("src.sources.rss.feedparser.parse", return_value=MOCK_FEED)
def test_rss_fetch_returns_events(mock_parse):
    source = RSSSource(["https://feeds.bbci.co.uk/news/rss.xml"])
    events = source.fetch()

    assert len(events) == 2
    assert events[0].title == "Earthquake hits Turkey"
    assert events[0].source == "BBC News"
    assert events[0].published_at == datetime(2026, 6, 5, 10, 0, 0, tzinfo=timezone.utc)


@patch("src.sources.rss.feedparser.parse", return_value=MOCK_FEED)
def test_rss_fetch_multiple_feeds(mock_parse):
    source = RSSSource(["https://feed1.com/rss", "https://feed2.com/rss"])
    events = source.fetch()

    assert len(events) == 4
    assert mock_parse.call_count == 2


@patch("src.sources.rss.feedparser.parse", return_value=EMPTY_FEED)
def test_rss_empty_feed_returns_no_events(mock_parse):
    source = RSSSource(["https://feeds.bbci.co.uk/news/rss.xml"])
    events = source.fetch()
    assert events == []


@patch("src.sources.rss.feedparser.parse", side_effect=Exception("Network error"))
def test_rss_failed_feed_does_not_raise(mock_parse):
    source = RSSSource(["https://broken-feed.com/rss"])
    events = source.fetch()
    assert events == []


@patch("src.sources.rss.feedparser.parse")
def test_rss_missing_published_date_uses_now(mock_parse):
    mock_parse.return_value = {
        "feed": {"title": "No Date Feed"},
        "entries": [{"title": "Undated article", "summary": "", "link": "https://x.com/1"}],
    }
    source = RSSSource(["https://nodatefeed.com/rss"])
    events = source.fetch()

    assert len(events) == 1
    assert events[0].published_at.tzinfo == timezone.utc
