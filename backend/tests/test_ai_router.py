import pytest
from unittest.mock import AsyncMock, patch

from app.models.problem import Challenge, ChallengeCollaborator, CollaboratorRole
from app.models.idea import Idea


def test_check_creativity(client_a, monkeypatch):
    mock_result = {
        "is_convergent": True,
        "reason": "Premature criticism",
        "suggested_alternative": "Try building on that idea instead",
    }
    monkeypatch.setattr(
        "app.ai.mediator.check_creativity",
        AsyncMock(return_value=mock_result),
    )
    res = client_a.post(
        "/api/ai/check-creativity",
        json={"content": "That won't work", "stage": "ideate"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_convergent"] is True
    assert "criticism" in data["reason"].lower()


def test_check_creativity_safe(client_a, monkeypatch):
    mock_result = {
        "is_convergent": False,
        "reason": "",
        "suggested_alternative": "",
    }
    monkeypatch.setattr(
        "app.ai.mediator.check_creativity",
        AsyncMock(return_value=mock_result),
    )
    res = client_a.post(
        "/api/ai/check-creativity",
        json={"content": "What if we try a different approach?"},
    )
    assert res.status_code == 200
    assert res.json()["is_convergent"] is False


def test_suggest_ideas(client_a, session, user_a, monkeypatch):
    c = Challenge(title="Test", description="Desc", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(
        challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner
    ))
    session.add(Idea(challenge_id=c.id, content="Existing idea", created_by=user_a.id))
    session.commit()

    mock_suggestions = [
        {"idea": "AI idea 1", "rationale": "Because"},
        {"idea": "AI idea 2", "rationale": "Why not"},
    ]
    monkeypatch.setattr(
        "app.ai.suggester.suggest_ideas",
        AsyncMock(return_value=mock_suggestions),
    )
    res = client_a.post(f"/api/ai/suggest-ideas/{c.id}")
    assert res.status_code == 200
    assert len(res.json()["suggestions"]) == 2


def test_suggest_ideas_not_collaborator(client_b, session, user_a):
    c = Challenge(title="Private", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(
        challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner
    ))
    session.commit()

    res = client_b.post(f"/api/ai/suggest-ideas/{c.id}")
    assert res.status_code == 403
