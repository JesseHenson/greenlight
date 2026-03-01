def test_me_returns_current_user(client_a, user_a):
    resp = client_a.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user_a.id
    assert data["name"] == "Alex"
    assert data["email"] == "a@test.com"
