import json

from app.models.problem import Challenge, ChallengeCollaborator, CollaboratorRole
from app.models.session import GreenlightSession, SessionStatus
from app.models.idea import Idea
from app.models.analysis import Analysis, AnalysisType


def test_get_idea_analyses(client_a, session, user_a):
    c = Challenge(title="T", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    idea = Idea(challenge_id=c.id, content="Test idea", created_by=user_a.id)
    session.add(idea)
    session.commit()
    session.refresh(idea)

    analysis = Analysis(
        idea_id=idea.id,
        analysis_type=AnalysisType.pros_cons,
        content=json.dumps({"pros": ["good"], "cons": ["bad"]}),
    )
    session.add(analysis)
    session.commit()

    res = client_a.get(f"/api/ideas/{idea.id}/analyses")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["analysis_type"] == "pros_cons"


def test_get_idea_analyses_not_collaborator(client_b, session, user_a):
    c = Challenge(title="T", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    idea = Idea(challenge_id=c.id, content="Test", created_by=user_a.id)
    session.add(idea)
    session.commit()
    session.refresh(idea)

    res = client_b.get(f"/api/ideas/{idea.id}/analyses")
    assert res.status_code == 403


def test_get_analysis_summary(client_a, session, user_a):
    c = Challenge(title="T", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.commit()

    summary = Analysis(
        challenge_id=c.id,
        analysis_type=AnalysisType.summary,
        content=json.dumps({"themes": ["speed"]}),
    )
    session.add(summary)
    session.commit()

    res = client_a.get(f"/api/challenges/{c.id}/analysis-summary")
    assert res.status_code == 200
    data = res.json()
    assert data["analysis_type"] == "summary"


def test_get_analysis_summary_none(client_a, session, user_a):
    c = Challenge(title="T", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.commit()

    res = client_a.get(f"/api/challenges/{c.id}/analysis-summary")
    assert res.status_code == 200
    assert res.json() is None


def test_get_analysis_status(client_a, session, user_a):
    c = Challenge(title="T", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    gs = GreenlightSession(challenge_id=c.id, status=SessionStatus.analysis_in_progress)
    session.add(gs)
    idea = Idea(challenge_id=c.id, content="Idea", created_by=user_a.id)
    session.add(idea)
    session.commit()
    session.refresh(idea)

    session.add(Analysis(
        idea_id=idea.id,
        analysis_type=AnalysisType.pros_cons,
        content="{}",
    ))
    session.commit()

    res = client_a.get(f"/api/challenges/{c.id}/analysis-status")
    assert res.status_code == 200
    data = res.json()
    assert data["session_status"] == "analysis_in_progress"
    assert data["total_analyses"] == 4  # 3 types + 1 summary
    assert data["completed_analyses"] == 1
    assert 0 < data["progress"] < 1
