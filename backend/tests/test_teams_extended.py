from app.models.group import PendingTeamInvite


def test_get_team(client_a, session, user_a, team_with_members):
    res = client_a.get(f"/api/teams/{team_with_members.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Test Team"
    assert len(data["members"]) == 2


def test_get_team_not_member(client_a, session, user_a):
    from app.models.group import Team
    t = Team(name="Other")
    session.add(t)
    session.commit()
    session.refresh(t)

    res = client_a.get(f"/api/teams/{t.id}")
    assert res.status_code == 403


def test_get_team_not_found(client_a):
    res = client_a.get("/api/teams/99999")
    assert res.status_code == 404


def test_update_team(client_a, session, user_a, team_with_members):
    res = client_a.patch(
        f"/api/teams/{team_with_members.id}",
        json={"name": "New Name"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"


def test_update_team_not_member(client_a, session, user_a):
    from app.models.group import Team
    t = Team(name="Other")
    session.add(t)
    session.commit()
    session.refresh(t)

    res = client_a.patch(f"/api/teams/{t.id}", json={"name": "Nope"})
    assert res.status_code == 403


def test_invite_existing_user(client_a, session, user_a, user_b, team_with_members):
    from app.models.user import User
    new_user = User(name="New", email="new@test.com", clerk_id="clerk_new")
    session.add(new_user)
    session.commit()

    res = client_a.post(
        f"/api/teams/{team_with_members.id}/invite",
        json={"email": "new@test.com"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "added"


def test_invite_already_member(client_a, session, user_a, user_b, team_with_members):
    res = client_a.post(
        f"/api/teams/{team_with_members.id}/invite",
        json={"email": user_b.email},
    )
    assert res.status_code == 400
    assert "Already a member" in res.json()["detail"]


def test_invite_unknown_email(client_a, session, user_a, team_with_members, monkeypatch):
    monkeypatch.setattr("app.routers.teams.send_clerk_invitation", lambda *a, **kw: None)
    res = client_a.post(
        f"/api/teams/{team_with_members.id}/invite",
        json={"email": "unknown@outside.com"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "invited"


def test_invite_duplicate_pending(client_a, session, user_a, team_with_members, monkeypatch):
    monkeypatch.setattr("app.routers.teams.send_clerk_invitation", lambda *a, **kw: None)
    client_a.post(
        f"/api/teams/{team_with_members.id}/invite",
        json={"email": "pending@test.com"},
    )
    res = client_a.post(
        f"/api/teams/{team_with_members.id}/invite",
        json={"email": "pending@test.com"},
    )
    assert res.status_code == 400
    assert "already been sent" in res.json()["detail"]


def test_list_pending_invites(client_a, session, user_a, team_with_members):
    session.add(PendingTeamInvite(
        group_id=team_with_members.id,
        email="pending@test.com",
        invited_by=user_a.id,
    ))
    session.commit()

    res = client_a.get(f"/api/teams/{team_with_members.id}/pending-invites")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["email"] == "pending@test.com"


def test_cancel_pending_invite(client_a, session, user_a, team_with_members):
    invite = PendingTeamInvite(
        group_id=team_with_members.id,
        email="cancel@test.com",
        invited_by=user_a.id,
    )
    session.add(invite)
    session.commit()
    session.refresh(invite)

    res = client_a.delete(f"/api/teams/{team_with_members.id}/pending-invites/{invite.id}")
    assert res.status_code == 200
    assert "cancelled" in res.json()["message"].lower()
