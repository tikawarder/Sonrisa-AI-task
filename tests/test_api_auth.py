import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.deps import get_current_user
from src.db.session import get_db
from src.db.models.user import User, UserRole
import uuid


def _make_user(**kwargs):
    defaults = dict(id=uuid.uuid4(), email="test@example.com", password="hashed", role=UserRole.USER)
    defaults.update(kwargs)
    return User(**defaults)


@pytest.fixture
def db_mock():
    return MagicMock()


@pytest.fixture
def client(db_mock):
    app.dependency_overrides[get_db] = lambda: db_mock
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestRegister:
    def test_register_new_user(self, client, db_mock):
        db_mock.query.return_value.filter.return_value.first.return_value = None
        with patch("src.api.routers.auth.hash_password", return_value="hashed"):
            resp = client.post("/auth/register", json={"email": "new@example.com", "password": "pass123"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert "id" in data
        db_mock.add.assert_called_once()
        db_mock.commit.assert_called_once()

    def test_register_duplicate_email(self, client, db_mock):
        db_mock.query.return_value.filter.return_value.first.return_value = _make_user()
        with patch("src.api.routers.auth.hash_password", return_value="hashed"):
            resp = client.post("/auth/register", json={"email": "dupe@example.com", "password": "pass123"})
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_register_invalid_email(self, client, db_mock):
        resp = client.post("/auth/register", json={"email": "not-an-email", "password": "pass123"})
        assert resp.status_code == 422


class TestLogin:
    def test_login_valid_credentials(self, client, db_mock):
        user = _make_user()
        db_mock.query.return_value.filter.return_value.first.return_value = user
        with patch("src.api.routers.auth.verify_password", return_value=True):
            resp = client.post("/auth/token", data={"username": "test@example.com", "password": "pass123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert resp.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, client, db_mock):
        user = _make_user()
        db_mock.query.return_value.filter.return_value.first.return_value = user
        with patch("src.api.routers.auth.verify_password", return_value=False):
            resp = client.post("/auth/token", data={"username": "test@example.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_unknown_user(self, client, db_mock):
        db_mock.query.return_value.filter.return_value.first.return_value = None
        resp = client.post("/auth/token", data={"username": "nobody@example.com", "password": "x"})
        assert resp.status_code == 401
