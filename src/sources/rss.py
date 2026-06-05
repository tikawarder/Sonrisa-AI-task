import logging
from datetime import datetime, timezone

import feedparser

from src.sources.base import Event, EventSource

logger = logging.getLogger(__name__)


class RSSSource(EventSource):
    def __init__(self, feed_urls: list[str]):
        self.feed_urls = feed_urls

    def fetch(self) -> list[Event]:
        events = []
        for url in self.feed_urls:
            try:
                events.extend(self._fetch_feed(url))
            except Exception as e:
                logger.warning("Failed to fetch RSS feed %s: %s", url, e)
        return events

    def _fetch_feed(self, url: str) -> list[Event]:
        feed = feedparser.parse(url)
        source_name = feed.get("feed", {}).get("title", url)
        return [
            Event(
                title=entry.get("title", ""),
                description=entry.get("summary", entry.get("description", "")),
                url=entry.get("link", ""),
                published_at=self._parse_date(entry),
                source=source_name,
            )
            for entry in feed.get("entries", [])
        ]

    def _parse_date(self, entry) -> datetime:
        published = entry.get("published_parsed")
        if published:
            return datetime(*published[:6], tzinfo=timezone.utc)
        return datetime.now(timezone.utc)
