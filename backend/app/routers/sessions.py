from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.approval import GateType, SessionApproval
from app.models.problem import ChallengeCollaborator
from app.models.session import GreenlightSession, SessionRead, SessionStatus
from app.models.user import User

router = APIRouter(tags=["sessions"])


def _current_gate(status: SessionStatus) -> GateType | None:
    if status == SessionStatus.ideate:
        return GateType.ideate_to_build
    elif status == SessionStatus.build:
        return GateType.build_to_converge
    return None


def _enrich_session(gs: GreenlightSession, session) -> SessionRead:
    """Build SessionRead with approval info for the current gate."""
    current_gate = _current_gate(gs.status)

    approvals = []
    if current_gate:
        approvals = session.exec(
            select(SessionApproval).where(
                SessionApproval.session_id == gs.id,
                SessionApproval.gate == current_gate,
            )
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
            select(ChallengeCollaborator).where(
                ChallengeCollaborator.challenge_id == gs.challenge_id
            )
        ).all()
    )

    return SessionRead(
        id=gs.id,
        challenge_id=gs.challenge_id,
        status=gs.status,
        approved_at=gs.approved_at,
        created_at=gs.created_at,
        approvals=approval_list,
        total_collaborators=total_collabs,
        all_approved=len(approvals) >= total_collabs,
    )


@router.get("/api/challenges/{challenge_id}/session", response_model=SessionRead)
def get_session_status(
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
    if not gs:
        raise HTTPException(status_code=404, detail="No session found")

    return _enrich_session(gs, session)


@router.post("/api/challenges/{challenge_id}/session/approve", response_model=SessionRead)
def approve_session(
    challenge_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
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
    if not gs:
        raise HTTPException(status_code=404, detail="No session found")

    current_gate = _current_gate(gs.status)
    if not current_gate:
        raise HTTPException(status_code=400, detail="Session is not in a gateable stage")

    # Check if user already approved this gate
    existing = session.exec(
        select(SessionApproval).where(
            SessionApproval.session_id == gs.id,
            SessionApproval.user_id == current_user.id,
            SessionApproval.gate == current_gate,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already approved")

    # Record this user's approval
    approval = SessionApproval(
        session_id=gs.id,
        user_id=current_user.id,
        gate=current_gate,
    )
    session.add(approval)
    session.commit()

    from app.services.notifications import notify_collaborators
    from app.models.notification import NotificationType
    gate_label = "definition" if current_gate == GateType.ideate_to_build else "analysis"
    notify_collaborators(
        session, challenge_id, current_user.id,
        NotificationType.approval_changed,
        f"{current_user.name} approved",
        f"Approved moving to the {gate_label} phase",
    )

    # Check if all collaborators have now approved this gate
    total_approvals = len(
        session.exec(
            select(SessionApproval).where(
                SessionApproval.session_id == gs.id,
                SessionApproval.gate == current_gate,
            )
        ).all()
    )
    total_collabs = len(
        session.exec(
            select(ChallengeCollaborator).where(
                ChallengeCollaborator.challenge_id == challenge_id
            )
        ).all()
    )

    if total_approvals >= total_collabs:
        if current_gate == GateType.ideate_to_build:
            gs.status = SessionStatus.build
            session.add(gs)
            session.commit()
            session.refresh(gs)
        elif current_gate == GateType.build_to_converge:
            gs.status = SessionStatus.approved_for_analysis
            gs.approved_at = datetime.utcnow()
            session.add(gs)
            session.commit()
            session.refresh(gs)

            # Kick off analysis in background
            from app.services.analysis_runner import run_analysis
            background_tasks.add_task(run_analysis, challenge_id)

    return _enrich_session(gs, session)
