def _create_problem_with_idea(client, group):
    problem = client.post("/api/problems", json={
        "title": "Test Problem",
        "description": "Test",
        "group_id": group.id,
    }).json()
    idea = client.post(f"/api/problems/{problem['id']}/ideas", json={
        "content": "Test idea",
    }).json()
    return problem, idea


def test_upsert_draft(client_a, group_with_parents):
    _, idea = _create_problem_with_idea(client_a, group_with_parents)

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


def test_draft_isolation(client_a, client_b, group_with_parents):
    """Parent A's draft should be invisible to Parent B."""
    _, idea = _create_problem_with_idea(client_a, group_with_parents)

    # Parent A writes a draft
    client_a.put(f"/api/ideas/{idea['id']}/draft", json={
        "notes": "A's secret thoughts",
    })

    # Parent B should see no draft (their own is empty)
    resp = client_b.get(f"/api/ideas/{idea['id']}/draft")
    assert resp.status_code == 200
    assert resp.json() is None

    # Parent B writes their own draft
    client_b.put(f"/api/ideas/{idea['id']}/draft", json={
        "notes": "B's private notes",
    })

    # Each parent sees only their own draft
    a_draft = client_a.get(f"/api/ideas/{idea['id']}/draft").json()
    b_draft = client_b.get(f"/api/ideas/{idea['id']}/draft").json()
    assert a_draft["notes"] == "A's secret thoughts"
    assert b_draft["notes"] == "B's private notes"
