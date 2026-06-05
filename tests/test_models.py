import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from src.db.models.alert import Alert
from src.db.models.channel import ChannelType, NotificationChannel
from src.db.models.matched_event import MatchedEvent
from src.db.models.notification_log import NotificationLog, NotificationStatus
from src.db.models.user import User, UserRole


def make_user(**kwargs) -> User:
    defaults = dict(id=uuid.uuid4(), email=f"{uuid.uuid4()}@test.com", password="hashed")
    return User(**{**defaults, **kwargs})


def test_create_user(db):
    user = make_user(role=UserRole.USER)
    db.add(user)
    db.flush()

    result = db.get(User, user.id)
    assert result is not None
    assert result.role == UserRole.USER
    assert result.created_at is not None


def test_user_email_unique_constraint(db):
    email = "duplicate@test.com"
    db.add(make_user(email=email))
    db.flush()

    db.add(make_user(email=email))
    with pytest.raises(IntegrityError):
        db.flush()


def test_alert_keywords_stored_as_array(db):
    user = make_user()
    db.add(user)
    db.flush()

    alert = Alert(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Earthquake Alert",
        keywords=["earthquake", "seismic", "magnitude"],
        use_llm=False,
        threshold=0.7,
    )
    db.add(alert)
    db.flush()

    result = db.get(Alert, alert.id)
    assert result is not None
    assert "earthquake" in result.keywords
    assert len(result.keywords) == 3
    assert result.is_active is True


def test_alert_defaults(db):
    user = make_user()
    db.add(user)
    db.flush()

    alert = Alert(id=uuid.uuid4(), user_id=user.id, name="Minimal Alert", keywords=[])
    db.add(alert)
    db.flush()

    result = db.get(Alert, alert.id)
    assert result.use_llm is False
    assert result.threshold == 0.7
    assert result.is_active is True


def test_channel_jsonb_config(db):
    user = make_user()
    db.add(user)
    db.flush()

    channel = NotificationChannel(
        id=uuid.uuid4(),
        user_id=user.id,
        type=ChannelType.EMAIL,
        config={"email": "notify@example.com"},
    )
    db.add(channel)
    db.flush()

    result = db.get(NotificationChannel, channel.id)
    assert result is not None
    assert result.config["email"] == "notify@example.com"
    assert result.type == ChannelType.EMAIL


def test_event_hash_deduplication(db):
    user = make_user()
    db.add(user)
    db.flush()

    alert = Alert(id=uuid.uuid4(), user_id=user.id, name="Test", keywords=["test"])
    db.add(alert)
    db.flush()

    db.add(MatchedEvent(id=uuid.uuid4(), alert_id=alert.id, event_hash="abc123"))
    db.flush()

    db.add(MatchedEvent(id=uuid.uuid4(), alert_id=alert.id, event_hash="abc123"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_notification_log_full_chain(db):
    user = make_user()
    db.add(user)
    db.flush()

    alert = Alert(id=uuid.uuid4(), user_id=user.id, name="Chain Test", keywords=["x"])
    channel = NotificationChannel(
        id=uuid.uuid4(),
        user_id=user.id,
        type=ChannelType.SLACK,
        config={"channel": "#alerts"},
    )
    db.add_all([alert, channel])
    db.flush()

    event = MatchedEvent(
        id=uuid.uuid4(),
        alert_id=alert.id,
        event_hash="chain-hash-001",
        event_title="Test Event",
        relevance_score=0.85,
    )
    db.add(event)
    db.flush()

    log = NotificationLog(
        id=uuid.uuid4(),
        matched_event_id=event.id,
        channel_id=channel.id,
        status=NotificationStatus.SENT,
    )
    db.add(log)
    db.flush()

    result = db.get(NotificationLog, log.id)
    assert result.status == NotificationStatus.SENT
    assert result.error_msg is None
