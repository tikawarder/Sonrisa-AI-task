import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.deps import require_admin_basic_auth, get_db
from src.db.models.alert import Alert
from src.db.models.user import User, UserRole


def _make_user():
    return User(
        id=uuid.uuid4(),
        email="admin@example.com",
        password="hashed",
        role=UserRole.ADMIN,
        created_at=datetime.now(timezone.utc),
    )


def _make_alert(user_id):
    return Alert(
        id=uuid.uuid4(),
        user_id=user_id,
        name="Test Alert",
        keywords=["flood"],
        topic="natural disasters",
        use_llm=False,
        threshold=0.7,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def db_mock():
    return MagicMock()


@pytest.fixture
def client(db_mock):
    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[require_admin_basic_auth] = lambda: "admin"
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestAdminAlertList:
    def test_alerts_page_returns_200(self, client, db_mock):
        db_mock.query.return_value.order_by.return_value.desc.return_value = MagicMock()
        db_mock.query.return_value.order_by.return_value.all.return_value = []
        db_mock.query.return_value.all.return_value = []
        resp = client.get("/admin/alerts")
        assert resp.status_code == 200

    def test_alerts_page_shows_alerts(self, client, db_mock):
        user = _make_user()
        alert = _make_alert(user.id)
        db_mock.query.return_value.order_by.return_value.all.return_value = [alert]
        db_mock.query.return_value.all.return_value = [user]
        resp = client.get("/admin/alerts")
        assert resp.status_code == 200
        assert "Test Alert" in resp.text


class TestAdminAlertCreate:
    def test_create_redirects_on_success(self, client, db_mock):
        user = _make_user()
        resp = client.post("/admin/alerts/create", data={
            "name": "New Alert",
            "keywords": "AI, robot",
            "topic": "artificial intelligence",
            "use_llm": "on",
            "threshold": "0.5",
            "user_id": str(user.id),
        }, follow_redirects=False)
        assert resp.status_code == 303
        assert resp.headers["location"] == "/admin/alerts"
        db_mock.add.assert_called_once()
        db_mock.commit.assert_called_once()

    def test_create_parses_keywords(self, client, db_mock):
        user = _make_user()
        client.post("/admin/alerts/create", data={
            "name": "KW Test",
            "keywords": "flood, earthquake, tsunami",
            "threshold": "0.7",
            "user_id": str(user.id),
        }, follow_redirects=False)
        added = db_mock.add.call_args[0][0]
        assert added.keywords == ["flood", "earthquake", "tsunami"]


class TestAdminAlertEdit:
    def test_edit_form_returns_200(self, client, db_mock):
        alert = _make_alert(uuid.uuid4())
        db_mock.get.return_value = alert
        resp = client.get(f"/admin/alerts/{alert.id}/edit")
        assert resp.status_code == 200
        assert "Test Alert" in resp.text

    def test_edit_form_404_redirects(self, client, db_mock):
        db_mock.get.return_value = None
        resp = client.get(f"/admin/alerts/{uuid.uuid4()}/edit", follow_redirects=False)
        assert resp.status_code == 303

    def test_update_saves_changes(self, client, db_mock):
        alert = _make_alert(uuid.uuid4())
        db_mock.get.return_value = alert
        resp = client.post(f"/admin/alerts/{alert.id}/edit", data={
            "name": "Updated Name",
            "keywords": "fire",
            "threshold": "0.6",
            "is_active": "on",
        }, follow_redirects=False)
        assert resp.status_code == 303
        assert alert.name == "Updated Name"
        assert alert.keywords == ["fire"]
        db_mock.commit.assert_called_once()


class TestAdminAlertDelete:
    def test_delete_removes_alert(self, client, db_mock):
        alert = _make_alert(uuid.uuid4())
        db_mock.get.return_value = alert
        resp = client.post(f"/admin/alerts/{alert.id}/delete", follow_redirects=False)
        assert resp.status_code == 303
        db_mock.delete.assert_called_once_with(alert)
        db_mock.commit.assert_called_once()

    def test_delete_missing_alert_still_redirects(self, client, db_mock):
        db_mock.get.return_value = None
        resp = client.post(f"/admin/alerts/{uuid.uuid4()}/delete", follow_redirects=False)
        assert resp.status_code == 303
        db_mock.delete.assert_not_called()
