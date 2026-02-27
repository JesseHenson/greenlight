from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.approval import SessionApproval
from app.models.problem import ProblemCollaborator
from app.models.session import BrainstormSession, SessionRead, SessionStatus
from app.models.user import User

router = APIRouter(tags=["sessions"])


def _enrich_session(bs: BrainstormSession, session) -> SessionRead:
    """Build SessionRead with approval info."""
    approvals = session.exec(
        select(SessionApproval).where(SessionApproval.session_id == bs.id)
    ).all()

    approval_list = []
    for a in approvals:
        u = session.get(User, a.user_id)
        approval_list.append({
            "user_id": a.user_id,
            "user_name": u.name if u else "Unknown",
            "approved_at": a.approved_at.isoformat(),
        })

    total_collabs = len(
        session.exec(
            select(ProblemCollaborator).where(
                ProblemCollaborator.problem_id == bs.problem_id
            )
        ).all()
    )

    return SessionRead(
        id=bs.id,
        problem_id=bs.problem_id,
        status=bs.status,
        approved_at=bs.approved_at,
        created_at=bs.created_at,
        approvals=approval_list,
        total_collaborators=total_collabs,
        all_approved=len(approvals) >= total_collabs,
    )


@router.get("/api/problems/{problem_id}/session", response_model=SessionRead)
def get_session_status(
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
    if not bs:
        raise HTTPException(status_code=404, detail="No session found")

    return _enrich_session(bs, session)


@router.post("/api/problems/{problem_id}/session/approve", response_model=SessionRead)
def approve_session(
    problem_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
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
    if not bs:
        raise HTTPException(status_code=404, detail="No session found")
    if bs.status != SessionStatus.brainstorming:
        raise HTTPException(status_code=400, detail="Session already approved")

    # Check if user already approved
    existing = session.exec(
        select(SessionApproval).where(
            SessionApproval.session_id == bs.id,
            SessionApproval.user_id == current_user.id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already approved")

    # Record this user's approval
    approval = SessionApproval(session_id=bs.id, user_id=current_user.id)
    session.add(approval)
    session.commit()

    # Check if all collaborators have now approved
    total_approvals = len(
        session.exec(
            select(SessionApproval).where(SessionApproval.session_id == bs.id)
        ).all()
    )
    total_collabs = len(
        session.exec(
            select(ProblemCollaborator).where(
                ProblemCollaborator.problem_id == problem_id
            )
        ).all()
    )

    if total_approvals >= total_collabs:
        bs.status = SessionStatus.approved_for_analysis
        bs.approved_at = datetime.utcnow()
        session.add(bs)
        session.commit()
        session.refresh(bs)

        # Kick off analysis in background
        from app.services.analysis_runner import run_analysis

        background_tasks.add_task(run_analysis, problem_id)

    return _enrich_session(bs, session)
