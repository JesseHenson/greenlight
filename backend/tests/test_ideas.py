def test_create_idea(client_a, group_with_parents):
    problem = client_a.post("/api/problems", json={
        "title": "Bedtime",
        "description": "Consistent bedtime",
        "group_id": group_with_parents.id,
    }).json()

    resp = client_a.post(f"/api/problems/{problem['id']}/ideas", json={
        "content": "8pm bedtime on school nights",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "8pm bedtime on school nights"
    assert data["tone_flag"] is False


def test_list_ideas(client_a, client_b, group_with_parents):
    problem = client_a.post("/api/problems", json={
        "title": "Bedtime",
        "description": "Consistent bedtime",
        "group_id": group_with_parents.id,
    }).json()
    pid = problem["id"]

    client_a.post(f"/api/problems/{pid}/ideas", json={"content": "Idea from A"})
    client_b.post(f"/api/problems/{pid}/ideas", json={"content": "Idea from B"})

    resp = client_a.get(f"/api/problems/{pid}/ideas")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_idea_clears_tone_flag(client_a, session, group_with_parents):
    from app.models.idea import BrainstormIdea

    problem = client_a.post("/api/problems", json={
        "title": "Test",
        "description": "Test",
        "group_id": group_with_parents.id,
    }).json()

    idea_resp = client_a.post(f"/api/problems/{problem['id']}/ideas", json={
        "content": "Original content",
    }).json()

    # Manually set tone_flag in DB to simulate flagged idea
    idea = session.get(BrainstormIdea, idea_resp["id"])
    idea.tone_flag = True
    idea.suggested_alternative = "Be nicer"
    session.add(idea)
    session.commit()

    # Update the idea — should clear tone flags
    resp = client_a.patch(f"/api/ideas/{idea_resp['id']}", json={
        "content": "Updated nicely",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["tone_flag"] is False
    assert data["suggested_alternative"] is None


def test_delete_idea(client_a, group_with_parents):
    problem = client_a.post("/api/problems", json={
        "title": "Test",
        "description": "Test",
        "group_id": group_with_parents.id,
    }).json()

    idea = client_a.post(f"/api/problems/{problem['id']}/ideas", json={
        "content": "To be deleted",
    }).json()

    resp = client_a.delete(f"/api/ideas/{idea['id']}")
    assert resp.status_code == 200

    ideas = client_a.get(f"/api/problems/{problem['id']}/ideas").json()
    assert len(ideas) == 0


def test_cannot_edit_others_idea(client_a, client_b, group_with_parents):
    problem = client_a.post("/api/problems", json={
        "title": "Test",
        "description": "Test",
        "group_id": group_with_parents.id,
    }).json()

    idea = client_a.post(f"/api/problems/{problem['id']}/ideas", json={
        "content": "A's idea",
    }).json()

    resp = client_b.patch(f"/api/ideas/{idea['id']}", json={
        "content": "B trying to edit",
    })
    assert resp.status_code == 403
