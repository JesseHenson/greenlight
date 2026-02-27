def test_create_problem(client_a, group_with_parents):
    resp = client_a.post("/api/problems", json={
        "title": "Bedtime Schedule",
        "description": "Need to agree on consistent bedtime",
        "group_id": group_with_parents.id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Bedtime Schedule"
    assert data["session_status"] == "brainstorming"


def test_list_problems(client_a, group_with_parents):
    client_a.post("/api/problems", json={
        "title": "Problem 1",
        "description": "Desc 1",
        "group_id": group_with_parents.id,
    })
    resp = client_a.get("/api/problems")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_problem(client_a, group_with_parents):
    create = client_a.post("/api/problems", json={
        "title": "Homework Routine",
        "description": "Need structure",
        "group_id": group_with_parents.id,
    })
    pid = create.json()["id"]
    resp = client_a.get(f"/api/problems/{pid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Homework Routine"


def test_update_problem(client_a, group_with_parents):
    create = client_a.post("/api/problems", json={
        "title": "Original",
        "description": "Desc",
        "group_id": group_with_parents.id,
    })
    pid = create.json()["id"]
    resp = client_a.patch(f"/api/problems/{pid}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_collaborator_can_view(client_a, client_b, group_with_parents):
    """Parent B (group member) should see problems created by Parent A."""
    create = client_a.post("/api/problems", json={
        "title": "Shared Problem",
        "description": "Both should see",
        "group_id": group_with_parents.id,
    })
    pid = create.json()["id"]

    resp = client_b.get(f"/api/problems/{pid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Shared Problem"


def test_non_collaborator_blocked(client_a, client_b):
    """Without a group, Parent B should NOT access Parent A's problem."""
    create = client_a.post("/api/problems", json={
        "title": "Private",
        "description": "Only A",
    })
    pid = create.json()["id"]

    resp = client_b.get(f"/api/problems/{pid}")
    assert resp.status_code == 403
