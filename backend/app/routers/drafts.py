from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.draft import IdeaDraft, IdeaDraftRead, IdeaDraftUpdate
from app.models.idea import Idea
from app.models.problem import ChallengeCollaborator
from app.models.session import GreenlightSession, SessionStatus

router = APIRouter(tags=["drafts"])


@router.get("/api/ideas/{idea_id}/draft", response_model=IdeaDraftRead | None)
def get_draft(idea_id: int, session: SessionDep, current_user: CurrentUser):
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

    draft = session.exec(
        select(IdeaDraft).where(
            IdeaDraft.idea_id == idea_id,
            IdeaDraft.user_id == current_user.id,
        )
    ).first()

    if not draft:
        return None

    return IdeaDraftRead(
        id=draft.id,
        idea_id=draft.idea_id,
        user_id=draft.user_id,
        notes=draft.notes,
        want_pros_cons=draft.want_pros_cons,
        want_feasibility=draft.want_feasibility,
        want_impact=draft.want_impact,
        updated_at=draft.updated_at,
    )


@router.put("/api/ideas/{idea_id}/draft", response_model=IdeaDraftRead)
def upsert_draft(
    idea_id: int,
    data: IdeaDraftUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
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

    # Allow drafts during ideate and build phases
    gs = session.exec(
        select(GreenlightSession).where(
            GreenlightSession.challenge_id == idea.challenge_id
        )
    ).first()
    if gs and gs.status not in (SessionStatus.ideate, SessionStatus.build):
        raise HTTPException(
            status_code=400, detail="Can only edit drafts during ideation and building"
        )

    draft = session.exec(
        select(IdeaDraft).where(
            IdeaDraft.idea_id == idea_id,
            IdeaDraft.user_id == current_user.id,
        )
    ).first()

    if draft:
        if data.notes is not None:
            draft.notes = data.notes
        if data.want_pros_cons is not None:
            draft.want_pros_cons = data.want_pros_cons
        if data.want_feasibility is not None:
            draft.want_feasibility = data.want_feasibility
        if data.want_impact is not None:
            draft.want_impact = data.want_impact
        draft.updated_at = datetime.utcnow()
    else:
        draft = IdeaDraft(
            idea_id=idea_id,
            user_id=current_user.id,
            notes=data.notes or "",
            want_pros_cons=data.want_pros_cons or False,
            want_feasibility=data.want_feasibility or False,
            want_impact=data.want_impact or False,
        )

    session.add(draft)
    session.commit()
    session.refresh(draft)

    return IdeaDraftRead(
        id=draft.id,
        idea_id=draft.idea_id,
        user_id=draft.user_id,
        notes=draft.notes,
        want_pros_cons=draft.want_pros_cons,
        want_feasibility=draft.want_feasibility,
        want_impact=draft.want_impact,
        updated_at=draft.updated_at,
    )
