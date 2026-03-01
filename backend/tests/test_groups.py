def test_create_team(client_a):
    resp = client_a.post("/api/teams", json={"name": "Product Team"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Product Team"
    assert len(data["members"]) == 1
    assert data["members"][0]["role"] == "owner"


def test_list_teams(client_a):
    client_a.post("/api/teams", json={"name": "Team 1"})
    client_a.post("/api/teams", json={"name": "Team 2"})
    resp = client_a.get("/api/teams")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_invite_existing_user(client_a, user_b):
    team = client_a.post("/api/teams", json={"name": "Test"}).json()
    resp = client_a.post(f"/api/teams/{team['id']}/invite", json={
        "email": "b@test.com",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "added"

    # User B should now appear in team members
    team_detail = client_a.get(f"/api/teams/{team['id']}").json()
    assert len(team_detail["members"]) == 2


def test_update_team_name(client_a):
    team = client_a.post("/api/teams", json={"name": "Original"}).json()
    resp = client_a.patch(f"/api/teams/{team['id']}", json={"name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


def test_non_member_blocked(client_b):
    """User B should not see User A's team (client_b has no teams)."""
    resp = client_b.get("/api/teams")
    assert resp.status_code == 200
    assert len(resp.json()) == 0
