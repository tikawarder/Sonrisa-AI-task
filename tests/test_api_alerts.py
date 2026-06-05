import uuid
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from src.api.main import app
from src.api.deps import get_current_user, get_db
from src.db.models.user import User, UserRole
from src.db.models.alert import Alert


def _make_user():
    return User(id=uuid.uuid4(), email="test@example.com", password="hashed", role=UserRole.USER)


def _make_alert(user_id, **kwargs):
    defaults = dict(
        id=uuid.uuid4(), user_id=user_id, name="Test Alert",
        keywords=["flood", "earthquake"], topic=None, use_llm=False,
        threshold=0.7, is_active=True, created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return Alert(**defaults)


@pytest.fixture
def user():
    return _make_user()


@pytest.fixture
def db_mock():
    return MagicMock()


@pytest.fixture
def client(db_mock, user):
    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: user
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestAlertCRUD:
    def test_list_alerts_empty(self, client, db_mock, user):
        db_mock.query.return_value.filter.return_value.all.return_value = []
        resp = client.get("/alerts/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_alerts_returns_own(self, client, db_mock, user):
        alerts = [_make_alert(user.id), _make_alert(user.id)]
        db_mock.query.return_value.filter.return_value.all.return_value = alerts
        resp = client.get("/alerts/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_create_alert(self, client, db_mock, user):
        resp = client.post("/alerts/", json={"name": "Flood Watch", "keywords": ["flood"]})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Flood Watch"
        assert data["keywords"] == ["flood"]
        db_mock.add.assert_called_once()
        db_mock.commit.assert_called_once()

    def test_get_alert_not_found(self, client, db_mock, user):
        db_mock.query.return_value.filter.return_value.first.return_value = None
        resp = client.get(f"/alerts/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_get_alert_found(self, client, db_mock, user):
        alert = _make_alert(user.id)
        db_mock.query.return_value.filter.return_value.first.return_value = alert
        resp = client.get(f"/alerts/{alert.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == alert.name

    def test_delete_alert(self, client, db_mock, user):
        alert = _make_alert(user.id)
        db_mock.query.return_value.filter.return_value.first.return_value = alert
        resp = client.delete(f"/alerts/{alert.id}")
        assert resp.status_code == 204
        db_mock.delete.assert_called_once_with(alert)

    def test_toggle_alert(self, client, db_mock, user):
        alert = _make_alert(user.id, is_active=True)
        db_mock.query.return_value.filter.return_value.first.return_value = alert
        resp = client.patch(f"/alerts/{alert.id}/toggle")
        assert resp.status_code == 200
        assert alert.is_active is False


class TestAlertAuth:
    def test_list_alerts_requires_auth(self, db_mock):
        app.dependency_overrides[get_db] = lambda: db_mock
        client = TestClient(app)
        resp = client.get("/alerts/")
        app.dependency_overrides.clear()
        assert resp.status_code == 401
