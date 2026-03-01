def _create_challenge_with_idea(client, team):
    challenge = client.post("/api/challenges", json={
        "title": "Test Challenge",
        "description": "Test",
        "group_id": team.id,
    }).json()
    idea = client.post(f"/api/challenges/{challenge['id']}/ideas", json={
        "content": "Test idea",
    }).json()
    return challenge, idea


def test_upsert_draft(client_a, team_with_members):
    _, idea = _create_challenge_with_idea(client_a, team_with_members)

    # Create
    resp = client_a.put(f"/api/ideas/{idea['id']}/draft", json={
        "notes": "My private notes",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["notes"] == "My private notes"

    # Update (upsert)
    resp = client_a.put(f"/api/ideas/{idea['id']}/draft", json={
        "notes": "Updated notes",
        "want_pros_cons": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["notes"] == "Updated notes"
    assert data["want_pros_cons"] is True


def test_draft_isolation(client_a, client_b, team_with_members):
    """User A's draft should be invisible to User B."""
    _, idea = _create_challenge_with_idea(client_a, team_with_members)

    # User A writes a draft
    client_a.put(f"/api/ideas/{idea['id']}/draft", json={
        "notes": "A's secret thoughts",
    })

    # User B should see no draft (their own is empty)
    resp = client_b.get(f"/api/ideas/{idea['id']}/draft")
    assert resp.status_code == 200
    assert resp.json() is None

    # User B writes their own draft
    client_b.put(f"/api/ideas/{idea['id']}/draft", json={
        "notes": "B's private notes",
    })

    # Each user sees only their own draft
    a_draft = client_a.get(f"/api/ideas/{idea['id']}/draft").json()
    b_draft = client_b.get(f"/api/ideas/{idea['id']}/draft").json()
    assert a_draft["notes"] == "A's secret thoughts"
    assert b_draft["notes"] == "B's private notes"
