"""Tests for auth endpoints and dev login."""

from app.models.user import User


def test_dev_login(client_a, session, user_a, monkeypatch):
    monkeypatch.setattr("app.routers.auth.settings.production", False)
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    res = client.post("/api/auth/dev-login", json={"email": user_a.email})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == user_a.email
    assert "token" in data


def test_dev_login_not_found(client_a, session, monkeypatch):
    monkeypatch.setattr("app.routers.auth.settings.production", False)
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    res = client.post("/api/auth/dev-login", json={"email": "nobody@test.com"})
    assert res.status_code == 404


def test_dev_login_blocked_in_production(client_a, session, user_a, monkeypatch):
    monkeypatch.setattr("app.routers.auth.settings.production", True)
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    res = client.post("/api/auth/dev-login", json={"email": user_a.email})
    assert res.status_code == 404
