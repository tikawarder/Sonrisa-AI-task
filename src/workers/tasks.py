import hashlib
import logging
import uuid

from src.core.config import settings
from src.db.models.alert import Alert
from src.db.models.channel import NotificationChannel as ChannelModel
from src.db.models.matched_event import MatchedEvent
from src.db.models.notification_log import NotificationLog, NotificationStatus
from src.db.session import SessionLocal
from src.matching.matcher import AlertConfig, AlertMatcher, LLMRelevanceScorer
from src.notifications.dispatcher import NotificationDispatcher
from src.sources.rss import RSSSource
from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.workers.tasks.fetch_and_dispatch")
def fetch_and_dispatch() -> dict:
    db = SessionLocal()
    matched_count = 0
    sent_count = 0

    try:
        events = RSSSource(settings.rss_feed_list).fetch()
        logger.info("Fetched %d events from RSS", len(events))

        db_alerts = db.query(Alert).filter(Alert.is_active.is_(True)).all()
        if not db_alerts:
            return {"matched": 0, "sent": 0}

        alert_configs = [
            AlertConfig(
                id=a.id,
                keywords=a.keywords or [],
                topic=a.topic,
                use_llm=a.use_llm,
                threshold=a.threshold,
            )
            for a in db_alerts
        ]

        llm_scorer = LLMRelevanceScorer(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None
        matches = AlertMatcher(llm_scorer=llm_scorer).match(events, alert_configs)

        dispatcher = NotificationDispatcher()

        for match in matches:
            event_hash = _hash(match.alert_id, match.event.url, str(match.event.published_at), match.event.title)

            if db.query(MatchedEvent).filter(MatchedEvent.event_hash == event_hash).first():
                continue

            matched_event = MatchedEvent(
                id=uuid.uuid4(),
                alert_id=match.alert_id,
                event_hash=event_hash,
                event_url=match.event.url,
                event_title=match.event.title,
                event_body=match.event.description,
                source=match.event.source,
                relevance_score=match.relevance_score,
            )
            db.add(matched_event)
            db.flush()
            matched_count += 1

            alert = db.get(Alert, match.alert_id)
            if not alert:
                continue

            channels = (
                db.query(ChannelModel)
                .filter(ChannelModel.user_id == alert.user_id, ChannelModel.is_active.is_(True))
                .all()
            )

            results = dispatcher.dispatch(
                subject=f"Alert: {match.event.title}",
                body=match.event.description or match.event.url,
                channels=channels,
            )

            for result in results:
                db.add(
                    NotificationLog(
                        id=uuid.uuid4(),
                        matched_event_id=matched_event.id,
                        channel_id=uuid.UUID(result.channel_id),
                        status=NotificationStatus.SENT if result.success else NotificationStatus.FAILED,
                        error_msg=result.error,
                    )
                )
                if result.success:
                    sent_count += 1

        db.commit()
        logger.info("Done — matched: %d, sent: %d", matched_count, sent_count)
        return {"matched": matched_count, "sent": sent_count}

    except Exception:
        db.rollback()
        logger.exception("fetch_and_dispatch failed")
        raise
    finally:
        db.close()


def _hash(alert_id, event_url: str, published_at: str, title: str = "") -> str:
    key = f"{alert_id}:{event_url}:{published_at}:{title}"
    return hashlib.sha256(key.encode()).hexdigest()
