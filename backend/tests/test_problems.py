def test_create_challenge(client_a, team_with_members):
    resp = client_a.post("/api/challenges", json={
        "title": "Reduce meeting fatigue",
        "description": "Need creative approaches to reduce meetings",
        "group_id": team_with_members.id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Reduce meeting fatigue"
    assert data["session_status"] == "ideate"


def test_list_challenges(client_a, team_with_members):
    client_a.post("/api/challenges", json={
        "title": "Challenge 1",
        "description": "Desc 1",
        "group_id": team_with_members.id,
    })
    resp = client_a.get("/api/challenges")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_challenge(client_a, team_with_members):
    create = client_a.post("/api/challenges", json={
        "title": "Onboarding redesign",
        "description": "Need better onboarding",
        "group_id": team_with_members.id,
    })
    cid = create.json()["id"]
    resp = client_a.get(f"/api/challenges/{cid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Onboarding redesign"


def test_update_challenge(client_a, team_with_members):
    create = client_a.post("/api/challenges", json={
        "title": "Original",
        "description": "Desc",
        "group_id": team_with_members.id,
    })
    cid = create.json()["id"]
    resp = client_a.patch(f"/api/challenges/{cid}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_collaborator_can_view(client_a, client_b, team_with_members):
    """User B (team member) should see challenges created by User A."""
    create = client_a.post("/api/challenges", json={
        "title": "Shared Challenge",
        "description": "Both should see",
        "group_id": team_with_members.id,
    })
    cid = create.json()["id"]

    resp = client_b.get(f"/api/challenges/{cid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Shared Challenge"


def test_non_collaborator_blocked(client_a, client_b):
    """Without a team, User B should NOT access User A's challenge."""
    create = client_a.post("/api/challenges", json={
        "title": "Private",
        "description": "Only A",
    })
    cid = create.json()["id"]

    resp = client_b.get(f"/api/challenges/{cid}")
    assert resp.status_code == 403
