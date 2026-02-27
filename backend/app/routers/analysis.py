from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.analysis import Analysis, AnalysisRead, AnalysisType
from app.models.idea import BrainstormIdea
from app.models.problem import ProblemCollaborator
from app.models.session import BrainstormSession

router = APIRouter(tags=["analysis"])


@router.get("/api/ideas/{idea_id}/analyses", response_model=list[AnalysisRead])
def get_idea_analyses(idea_id: int, session: SessionDep, current_user: CurrentUser):
    idea = session.get(BrainstormIdea, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    collab = session.exec(
        select(ProblemCollaborator).where(
            ProblemCollaborator.problem_id == idea.problem_id,
            ProblemCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")

    analyses = session.exec(
        select(Analysis).where(Analysis.brainstorm_idea_id == idea_id)
    ).all()
    return analyses


@router.get("/api/problems/{problem_id}/analysis-summary", response_model=AnalysisRead | None)
def get_analysis_summary(
    problem_id: int, session: SessionDep, current_user: CurrentUser
):
    collab = session.exec(
        select(ProblemCollaborator).where(
            ProblemCollaborator.problem_id == problem_id,
            ProblemCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")

    summary = session.exec(
        select(Analysis).where(
            Analysis.problem_id == problem_id,
            Analysis.analysis_type == AnalysisType.summary,
        )
    ).first()
    return summary


@router.get("/api/problems/{problem_id}/analysis-status")
def get_analysis_status(
    problem_id: int, session: SessionDep, current_user: CurrentUser
):
    collab = session.exec(
        select(ProblemCollaborator).where(
            ProblemCollaborator.problem_id == problem_id,
            ProblemCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")

    bs = session.exec(
        select(BrainstormSession).where(BrainstormSession.problem_id == problem_id)
    ).first()

    ideas = session.exec(
        select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
    ).all()
    total_expected = len(ideas) * 3 + 1  # 3 types per idea + 1 summary
    completed = len(
        session.exec(
            select(Analysis).where(
                (Analysis.problem_id == problem_id)
                | (Analysis.brainstorm_idea_id.in_([i.id for i in ideas]))  # type: ignore
            )
        ).all()
    )

    return {
        "session_status": bs.status if bs else None,
        "total_analyses": total_expected,
        "completed_analyses": completed,
        "progress": completed / total_expected if total_expected > 0 else 0,
    }
