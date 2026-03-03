from app.models.problem import Challenge, ChallengeCollaborator, CollaboratorRole, ChallengeStatus
from app.models.session import GreenlightSession
from app.models.idea import Idea
from app.models.comment import Comment
from app.models.analysis import Analysis, AnalysisType


def test_archive_challenge(client_a, session, user_a):
    c = Challenge(title="Archive Me", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.commit()

    res = client_a.post(f"/api/challenges/{c.id}/archive")
    assert res.status_code == 200
    assert "archived" in res.json()["message"].lower()


def test_archive_not_creator(client_b, session, user_a, user_b):
    c = Challenge(title="Not Mine", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_b.id, role=CollaboratorRole.collaborator))
    session.commit()

    res = client_b.post(f"/api/challenges/{c.id}/archive")
    assert res.status_code == 403


def test_delete_challenge(client_a, session, user_a):
    c = Challenge(title="Delete Me", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    gs = GreenlightSession(challenge_id=c.id)
    session.add(gs)
    idea = Idea(challenge_id=c.id, content="Idea", created_by=user_a.id)
    session.add(idea)
    session.commit()
    session.refresh(idea)
    session.add(Comment(idea_id=idea.id, content="Comment", created_by=user_a.id))
    session.add(Analysis(idea_id=idea.id, analysis_type=AnalysisType.pros_cons, content="{}"))
    session.commit()

    res = client_a.post(
        f"/api/challenges/{c.id}/delete",
        json={"password": "confirm-delete"},
    )
    assert res.status_code == 200
    assert "permanently deleted" in res.json()["message"].lower()


def test_delete_wrong_password(client_a, session, user_a):
    c = Challenge(title="Nope", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.commit()

    res = client_a.post(
        f"/api/challenges/{c.id}/delete",
        json={"password": "wrong"},
    )
    assert res.status_code == 403


def test_add_collaborator(client_a, session, user_a, user_b):
    c = Challenge(title="Collab", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.commit()

    res = client_a.post(
        f"/api/challenges/{c.id}/collaborators",
        json={"email": user_b.email},
    )
    assert res.status_code == 200
    assert user_b.name in res.json()["message"]


def test_add_collaborator_already_exists(client_a, session, user_a, user_b):
    c = Challenge(title="Dup Collab", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_b.id, role=CollaboratorRole.collaborator))
    session.commit()

    res = client_a.post(
        f"/api/challenges/{c.id}/collaborators",
        json={"email": user_b.email},
    )
    assert res.status_code == 400


def test_add_collaborator_unknown_email(client_a, session, user_a):
    c = Challenge(title="Unknown", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.commit()

    res = client_a.post(
        f"/api/challenges/{c.id}/collaborators",
        json={"email": "nobody@test.com"},
    )
    assert res.status_code == 404


def test_create_challenge_with_team(client_a, session, user_a, team_with_members):
    res = client_a.post("/api/challenges", json={
        "title": "Team Challenge",
        "description": "Shared with team",
        "group_id": team_with_members.id,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Team Challenge"
    assert data["session_status"] == "ideate"
