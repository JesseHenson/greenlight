def test_create_and_list_comments(client_a, client_b, team_with_members):
    challenge = client_a.post("/api/challenges", json={
        "title": "Test",
        "description": "Test",
        "group_id": team_with_members.id,
    }).json()

    idea = client_a.post(f"/api/challenges/{challenge['id']}/ideas", json={
        "content": "An idea",
    }).json()

    # Both teammates comment
    resp_a = client_a.post(f"/api/ideas/{idea['id']}/comments", json={
        "content": "I like this idea",
    })
    assert resp_a.status_code == 200

    resp_b = client_b.post(f"/api/ideas/{idea['id']}/comments", json={
        "content": "Me too",
    })
    assert resp_b.status_code == 200

    # List comments
    resp = client_a.get(f"/api/ideas/{idea['id']}/comments")
    assert resp.status_code == 200
    comments = resp.json()
    assert len(comments) == 2
    assert comments[0]["content"] == "I like this idea"
    assert comments[1]["content"] == "Me too"


def test_non_collaborator_cannot_comment(client_a, client_b):
    """User B (not a collaborator) should not be able to comment."""
    challenge = client_a.post("/api/challenges", json={
        "title": "Private",
        "description": "Only A",
    }).json()

    idea = client_a.post(f"/api/challenges/{challenge['id']}/ideas", json={
        "content": "Private idea",
    }).json()

    resp = client_b.post(f"/api/ideas/{idea['id']}/comments", json={
        "content": "Sneaky comment",
    })
    assert resp.status_code == 403
