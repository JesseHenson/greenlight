"""Tests for the analysis runner service with mocked AI calls."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.models.problem import Challenge, ChallengeCollaborator, CollaboratorRole
from app.models.session import GreenlightSession, SessionStatus
from app.models.idea import Idea
from app.models.analysis import Analysis, AnalysisType
from app.models.user import User


@pytest.fixture
def runner_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def runner_session(runner_engine):
    with Session(runner_engine) as session:
        yield session


def _setup_challenge(session):
    """Create a challenge with session and ideas for analysis."""
    user = User(name="Test", email="runner@test.com", clerk_id="clerk_runner")
    session.add(user)
    session.commit()
    session.refresh(user)

    c = Challenge(title="Analyze Me", description="A test challenge", created_by=user.id)
    session.add(c)
    session.commit()
    session.refresh(c)

    session.add(ChallengeCollaborator(
        challenge_id=c.id, user_id=user.id, role=CollaboratorRole.owner
    ))

    gs = GreenlightSession(challenge_id=c.id, status=SessionStatus.approved_for_analysis)
    session.add(gs)

    idea = Idea(challenge_id=c.id, content="Test idea", created_by=user.id)
    session.add(idea)
    session.commit()
    session.refresh(idea)

    return c, gs, idea


@pytest.mark.asyncio
async def test_run_analysis_full(runner_engine, runner_session):
    c, gs, idea = _setup_challenge(runner_session)

    mock_analyze = AsyncMock(return_value='{"pros": ["good"], "cons": ["bad"]}')
    mock_summarize = AsyncMock(return_value='{"themes": ["speed"]}')

    with patch("app.services.analysis_runner.engine", runner_engine), \
         patch("app.services.analysis_runner.analyze_idea", mock_analyze), \
         patch("app.services.analysis_runner.summarize_session", mock_summarize):
        from app.services.analysis_runner import _run_analysis_async
        await _run_analysis_async(c.id)

    # Verify analyses were created
    with Session(runner_engine) as s:
        analyses = s.exec(select(Analysis).where(Analysis.idea_id == idea.id)).all()
        assert len(analyses) == 3  # pros_cons, feasibility, impact

        summary = s.exec(
            select(Analysis).where(
                Analysis.challenge_id == c.id,
                Analysis.analysis_type == AnalysisType.summary,
            )
        ).first()
        assert summary is not None

        gs_updated = s.exec(
            select(GreenlightSession).where(GreenlightSession.challenge_id == c.id)
        ).first()
        assert gs_updated.status == SessionStatus.analysis_complete


@pytest.mark.asyncio
async def test_run_analysis_no_session(runner_engine, runner_session):
    """Should return early if no greenlight session exists."""
    mock_analyze = AsyncMock()

    with patch("app.services.analysis_runner.engine", runner_engine), \
         patch("app.services.analysis_runner.analyze_idea", mock_analyze):
        from app.services.analysis_runner import _run_analysis_async
        await _run_analysis_async(99999)

    mock_analyze.assert_not_called()


@pytest.mark.asyncio
async def test_run_analysis_handles_analyze_error(runner_engine, runner_session):
    c, gs, idea = _setup_challenge(runner_session)

    mock_analyze = AsyncMock(side_effect=Exception("AI Error"))
    mock_summarize = AsyncMock(return_value='{"themes": []}')

    with patch("app.services.analysis_runner.engine", runner_engine), \
         patch("app.services.analysis_runner.analyze_idea", mock_analyze), \
         patch("app.services.analysis_runner.summarize_session", mock_summarize), \
         patch("app.services.analysis_runner.sentry_sdk"):
        from app.services.analysis_runner import _run_analysis_async
        await _run_analysis_async(c.id)

    # Should still complete even if analyses fail
    with Session(runner_engine) as s:
        gs_updated = s.exec(
            select(GreenlightSession).where(GreenlightSession.challenge_id == c.id)
        ).first()
        assert gs_updated.status == SessionStatus.analysis_complete


@pytest.mark.asyncio
async def test_run_analysis_handles_summary_error(runner_engine, runner_session):
    c, gs, idea = _setup_challenge(runner_session)

    mock_analyze = AsyncMock(return_value='{"score": 7}')
    mock_summarize = AsyncMock(side_effect=Exception("Summary Error"))

    with patch("app.services.analysis_runner.engine", runner_engine), \
         patch("app.services.analysis_runner.analyze_idea", mock_analyze), \
         patch("app.services.analysis_runner.summarize_session", mock_summarize), \
         patch("app.services.analysis_runner.sentry_sdk"):
        from app.services.analysis_runner import _run_analysis_async
        await _run_analysis_async(c.id)

    with Session(runner_engine) as s:
        gs_updated = s.exec(
            select(GreenlightSession).where(GreenlightSession.challenge_id == c.id)
        ).first()
        assert gs_updated.status == SessionStatus.analysis_complete
