from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_join_waitlist():
    res = client.post("/api/waitlist", json={"name": "Test User", "email": "wait@test.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Test User"
    assert data["email"] == "wait@test.com"
    assert "id" in data


def test_join_waitlist_duplicate():
    client.post("/api/waitlist", json={"name": "First", "email": "dup@test.com"})
    res = client.post("/api/waitlist", json={"name": "Second", "email": "dup@test.com"})
    assert res.status_code == 409
    assert "already on the waitlist" in res.json()["detail"]


def test_list_waitlist():
    client.post("/api/waitlist", json={"name": "User A", "email": "a-list@test.com"})
    client.post("/api/waitlist", json={"name": "User B", "email": "b-list@test.com"})
    res = client.get("/api/waitlist")
    assert res.status_code == 200
    emails = [e["email"] for e in res.json()]
    assert "a-list@test.com" in emails
    assert "b-list@test.com" in emails


def test_waitlist_count():
    client.post("/api/waitlist", json={"name": "Counter", "email": "count@test.com"})
    res = client.get("/api/waitlist/count")
    assert res.status_code == 200
    assert res.json()["count"] >= 1


def test_remove_from_waitlist():
    res = client.post("/api/waitlist", json={"name": "Removable", "email": "remove@test.com"})
    entry_id = res.json()["id"]
    res = client.delete(f"/api/waitlist/{entry_id}")
    assert res.status_code == 200
    assert "Removed" in res.json()["message"]


def test_remove_nonexistent():
    res = client.delete("/api/waitlist/99999")
    assert res.status_code == 404
