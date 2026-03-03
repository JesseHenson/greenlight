from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.idea import Idea, IdeaCreate, IdeaRead
from app.models.problem import ChallengeCollaborator
from app.models.session import GreenlightSession, SessionStatus
from app.models.user import User

router = APIRouter(tags=["ideas"])


def _check_collaborator(session, challenge_id: int, user_id: int):
    collab = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == challenge_id,
            ChallengeCollaborator.user_id == user_id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")


def _enrich_idea(idea: Idea, session) -> IdeaRead:
    creator = session.get(User, idea.created_by)
    return IdeaRead(
        id=idea.id,
        challenge_id=idea.challenge_id,
        content=idea.content,
        created_by=idea.created_by,
        creator_name=creator.name if creator else None,
        status=idea.status,
        tone_flag=idea.tone_flag,
        suggested_alternative=idea.suggested_alternative,
        created_at=idea.created_at,
    )


@router.post("/api/challenges/{challenge_id}/ideas", response_model=IdeaRead)
def create_idea(
    challenge_id: int,
    data: IdeaCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    _check_collaborator(session, challenge_id, current_user.id)

    # Allow idea creation during ideate and build phases
    gs = session.exec(
        select(GreenlightSession).where(GreenlightSession.challenge_id == challenge_id)
    ).first()
    if gs and gs.status not in (SessionStatus.ideate, SessionStatus.build):
        raise HTTPException(
            status_code=400,
            detail="Idea phase has ended. Cannot add new ideas.",
        )

    idea = Idea(
        challenge_id=challenge_id,
        content=data.content,
        created_by=current_user.id,
    )
    session.add(idea)
    session.commit()
    session.refresh(idea)

    from app.services.notifications import notify_collaborators
    from app.models.notification import NotificationType
    preview = data.content[:80] + ("..." if len(data.content) > 80 else "")
    notify_collaborators(
        session, challenge_id, current_user.id,
        NotificationType.idea_added,
        f"{current_user.name} added an idea",
        preview,
    )

    from app.services.sse import broadcast
    broadcast(challenge_id, "idea_added", {"idea_id": idea.id})

    return _enrich_idea(idea, session)


@router.get("/api/challenges/{challenge_id}/ideas", response_model=list[IdeaRead])
def list_ideas(challenge_id: int, session: SessionDep, current_user: CurrentUser):
    _check_collaborator(session, challenge_id, current_user.id)
    ideas = session.exec(
        select(Idea).where(Idea.challenge_id == challenge_id)
    ).all()
    return [_enrich_idea(i, session) for i in ideas]


@router.patch("/api/ideas/{idea_id}", response_model=IdeaRead)
def update_idea(
    idea_id: int,
    data: IdeaCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    idea = session.get(Idea, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    if idea.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own ideas")
    idea.content = data.content
    idea.tone_flag = False
    idea.suggested_alternative = None
    session.add(idea)
    session.commit()
    session.refresh(idea)

    from app.services.sse import broadcast
    broadcast(idea.challenge_id, "idea_updated", {"idea_id": idea.id})

    return _enrich_idea(idea, session)


@router.delete("/api/ideas/{idea_id}")
def delete_idea(idea_id: int, session: SessionDep, current_user: CurrentUser):
    idea = session.get(Idea, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    if idea.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own ideas")

    # Cascade delete drafts
    from app.models.draft import IdeaDraft

    for draft in session.exec(
        select(IdeaDraft).where(IdeaDraft.idea_id == idea_id)
    ).all():
        session.delete(draft)

    challenge_id = idea.challenge_id
    session.delete(idea)
    session.commit()

    from app.services.sse import broadcast
    broadcast(challenge_id, "idea_deleted", {"idea_id": idea_id})

    return {"message": "Idea deleted"}
