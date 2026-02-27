def test_create_group(client_a):
    resp = client_a.post("/api/groups", json={"name": "Our Family"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Our Family"
    assert len(data["members"]) == 1
    assert data["members"][0]["role"] == "owner"


def test_list_groups(client_a):
    client_a.post("/api/groups", json={"name": "Family 1"})
    client_a.post("/api/groups", json={"name": "Family 2"})
    resp = client_a.get("/api/groups")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_invite_existing_user(client_a, parent_b):
    group = client_a.post("/api/groups", json={"name": "Test"}).json()
    resp = client_a.post(f"/api/groups/{group['id']}/invite", json={
        "email": "b@test.com",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "added"

    # Parent B should now appear in group members
    group_detail = client_a.get(f"/api/groups/{group['id']}").json()
    assert len(group_detail["members"]) == 2


def test_update_group_name(client_a):
    group = client_a.post("/api/groups", json={"name": "Original"}).json()
    resp = client_a.patch(f"/api/groups/{group['id']}", json={"name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


def test_non_member_blocked(client_b):
    """Parent B should not see Parent A's group (client_b has no groups)."""
    resp = client_b.get("/api/groups")
    assert resp.status_code == 200
    assert len(resp.json()) == 0
