from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.analysis import Analysis, AnalysisRead, AnalysisType
from app.models.idea import Idea
from app.models.problem import ChallengeCollaborator
from app.models.session import GreenlightSession

router = APIRouter(tags=["analysis"])


@router.get("/api/ideas/{idea_id}/analyses", response_model=list[AnalysisRead])
def get_idea_analyses(idea_id: int, session: SessionDep, current_user: CurrentUser):
    idea = session.get(Idea, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    collab = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == idea.challenge_id,
            ChallengeCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")

    analyses = session.exec(
        select(Analysis).where(Analysis.idea_id == idea_id)
    ).all()
    return analyses


@router.get("/api/challenges/{challenge_id}/analysis-summary", response_model=AnalysisRead | None)
def get_analysis_summary(
    challenge_id: int, session: SessionDep, current_user: CurrentUser
):
    collab = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == challenge_id,
            ChallengeCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")

    summary = session.exec(
        select(Analysis).where(
            Analysis.challenge_id == challenge_id,
            Analysis.analysis_type == AnalysisType.summary,
        )
    ).first()
    return summary


@router.get("/api/challenges/{challenge_id}/analysis-status")
def get_analysis_status(
    challenge_id: int, session: SessionDep, current_user: CurrentUser
):
    collab = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == challenge_id,
            ChallengeCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")

    gs = session.exec(
        select(GreenlightSession).where(GreenlightSession.challenge_id == challenge_id)
    ).first()

    ideas = session.exec(
        select(Idea).where(Idea.challenge_id == challenge_id)
    ).all()
    total_expected = len(ideas) * 3 + 1  # 3 types per idea + 1 summary
    completed = len(
        session.exec(
            select(Analysis).where(
                (Analysis.challenge_id == challenge_id)
                | (Analysis.idea_id.in_([i.id for i in ideas]))  # type: ignore
            )
        ).all()
    )

    return {
        "session_status": gs.status if gs else None,
        "total_analyses": total_expected,
        "completed_analyses": completed,
        "progress": completed / total_expected if total_expected > 0 else 0,
    }
