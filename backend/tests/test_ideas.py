def test_create_idea(client_a, team_with_members):
    challenge = client_a.post("/api/challenges", json={
        "title": "Meeting fatigue",
        "description": "Too many meetings",
        "group_id": team_with_members.id,
    }).json()

    resp = client_a.post(f"/api/challenges/{challenge['id']}/ideas", json={
        "content": "Replace all recurring meetings with async video updates",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "Replace all recurring meetings with async video updates"
    assert data["tone_flag"] is False


def test_list_ideas(client_a, client_b, team_with_members):
    challenge = client_a.post("/api/challenges", json={
        "title": "Meeting fatigue",
        "description": "Too many meetings",
        "group_id": team_with_members.id,
    }).json()
    cid = challenge["id"]

    client_a.post(f"/api/challenges/{cid}/ideas", json={"content": "Idea from A"})
    client_b.post(f"/api/challenges/{cid}/ideas", json={"content": "Idea from B"})

    resp = client_a.get(f"/api/challenges/{cid}/ideas")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_idea_clears_tone_flag(client_a, session, team_with_members):
    from app.models.idea import Idea

    challenge = client_a.post("/api/challenges", json={
        "title": "Test",
        "description": "Test",
        "group_id": team_with_members.id,
    }).json()

    idea_resp = client_a.post(f"/api/challenges/{challenge['id']}/ideas", json={
        "content": "Original content",
    }).json()

    # Manually set tone_flag in DB to simulate flagged idea
    idea = session.get(Idea, idea_resp["id"])
    idea.tone_flag = True
    idea.suggested_alternative = "Try building instead"
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


def test_delete_idea(client_a, team_with_members):
    challenge = client_a.post("/api/challenges", json={
        "title": "Test",
        "description": "Test",
        "group_id": team_with_members.id,
    }).json()

    idea = client_a.post(f"/api/challenges/{challenge['id']}/ideas", json={
        "content": "To be deleted",
    }).json()

    resp = client_a.delete(f"/api/ideas/{idea['id']}")
    assert resp.status_code == 200

    ideas = client_a.get(f"/api/challenges/{challenge['id']}/ideas").json()
    assert len(ideas) == 0


def test_cannot_edit_others_idea(client_a, client_b, team_with_members):
    challenge = client_a.post("/api/challenges", json={
        "title": "Test",
        "description": "Test",
        "group_id": team_with_members.id,
    }).json()

    idea = client_a.post(f"/api/challenges/{challenge['id']}/ideas", json={
        "content": "A's idea",
    }).json()

    resp = client_b.patch(f"/api/ideas/{idea['id']}", json={
        "content": "B trying to edit",
    })
    assert resp.status_code == 403
