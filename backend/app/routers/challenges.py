from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.problem import (
    Challenge,
    ChallengeCollaborator,
    ChallengeCreate,
    ChallengeRead,
    ChallengeUpdate,
    ChallengeStatus,
    CollaboratorRole,
)
from app.models.session import GreenlightSession, SessionStatus
from app.models.idea import Idea
from app.models.user import User
from app.models.group import TeamMember

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.post("", response_model=ChallengeRead)
def create_challenge(data: ChallengeCreate, session: SessionDep, current_user: CurrentUser):
    challenge = Challenge(
        title=data.title,
        description=data.description,
        created_by=current_user.id,
        group_id=data.group_id,
    )
    session.add(challenge)
    session.commit()
    session.refresh(challenge)

    # Auto-add owner as collaborator
    collab = ChallengeCollaborator(
        challenge_id=challenge.id,
        user_id=current_user.id,
        role=CollaboratorRole.owner,
    )
    session.add(collab)

    # If group_id provided, auto-add all team members as collaborators
    if data.group_id:
        team_members = session.exec(
            select(TeamMember).where(TeamMember.group_id == data.group_id)
        ).all()
        for tm in team_members:
            if tm.user_id != current_user.id:
                session.add(ChallengeCollaborator(
                    challenge_id=challenge.id,
                    user_id=tm.user_id,
                    role=CollaboratorRole.collaborator,
                ))

    # Auto-create greenlight session with ideate status
    gs = GreenlightSession(challenge_id=challenge.id)
    session.add(gs)
    session.commit()

    return ChallengeRead(
        id=challenge.id,
        title=challenge.title,
        description=challenge.description,
        status=challenge.status,
        created_by=challenge.created_by,
        created_at=challenge.created_at,
        idea_count=0,
        session_status=gs.status,
    )


@router.get("", response_model=list[ChallengeRead])
def list_challenges(session: SessionDep, current_user: CurrentUser):
    stmt = (
        select(Challenge)
        .join(ChallengeCollaborator, ChallengeCollaborator.challenge_id == Challenge.id)
        .where(
            ChallengeCollaborator.user_id == current_user.id,
            Challenge.status == ChallengeStatus.active,
        )
    )
    challenges = session.exec(stmt).all()
    result = []
    for c in challenges:
        idea_count = len(
            session.exec(
                select(Idea).where(Idea.challenge_id == c.id)
            ).all()
        )
        gs = session.exec(
            select(GreenlightSession).where(GreenlightSession.challenge_id == c.id)
        ).first()
        result.append(
            ChallengeRead(
                id=c.id,
                title=c.title,
                description=c.description,
                status=c.status,
                created_by=c.created_by,
                created_at=c.created_at,
                idea_count=idea_count,
                session_status=gs.status if gs else None,
            )
        )
    return result


@router.get("/{challenge_id}", response_model=ChallengeRead)
def get_challenge(challenge_id: int, session: SessionDep, current_user: CurrentUser):
    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    collab = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == challenge_id,
            ChallengeCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator on this challenge")

    idea_count = len(
        session.exec(
            select(Idea).where(Idea.challenge_id == challenge_id)
        ).all()
    )
    gs = session.exec(
        select(GreenlightSession).where(GreenlightSession.challenge_id == challenge_id)
    ).first()

    return ChallengeRead(
        id=challenge.id,
        title=challenge.title,
        description=challenge.description,
        status=challenge.status,
        created_by=challenge.created_by,
        created_at=challenge.created_at,
        idea_count=idea_count,
        session_status=gs.status if gs else None,
    )


@router.patch("/{challenge_id}", response_model=ChallengeRead)
def update_challenge(
    challenge_id: int,
    data: ChallengeUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if challenge.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can edit")

    if data.title is not None:
        challenge.title = data.title
    if data.description is not None:
        challenge.description = data.description
    session.add(challenge)
    session.commit()
    session.refresh(challenge)

    idea_count = len(
        session.exec(
            select(Idea).where(Idea.challenge_id == challenge_id)
        ).all()
    )
    gs = session.exec(
        select(GreenlightSession).where(GreenlightSession.challenge_id == challenge_id)
    ).first()

    return ChallengeRead(
        id=challenge.id,
        title=challenge.title,
        description=challenge.description,
        status=challenge.status,
        created_by=challenge.created_by,
        created_at=challenge.created_at,
        idea_count=idea_count,
        session_status=gs.status if gs else None,
    )


@router.post("/{challenge_id}/archive")
def archive_challenge(challenge_id: int, session: SessionDep, current_user: CurrentUser):
    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if challenge.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can archive")
    challenge.status = ChallengeStatus.archived
    session.add(challenge)
    session.commit()
    return {"message": "Challenge archived"}


from pydantic import BaseModel as PydanticBaseModel


class DeleteRequest(PydanticBaseModel):
    password: str


DELETE_PASSWORD = "confirm-delete"


@router.post("/{challenge_id}/delete")
def delete_challenge(
    challenge_id: int,
    data: DeleteRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if challenge.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can delete")
    if data.password != DELETE_PASSWORD:
        raise HTTPException(status_code=403, detail="Incorrect delete password")

    from app.models.comment import Comment
    from app.models.analysis import Analysis
    from app.models.draft import IdeaDraft
    from app.models.approval import SessionApproval

    ideas = session.exec(
        select(Idea).where(Idea.challenge_id == challenge_id)
    ).all()
    for idea in ideas:
        for draft in session.exec(select(IdeaDraft).where(IdeaDraft.idea_id == idea.id)).all():
            session.delete(draft)
        for comment in session.exec(select(Comment).where(Comment.idea_id == idea.id)).all():
            session.delete(comment)
        for analysis in session.exec(select(Analysis).where(Analysis.idea_id == idea.id)).all():
            session.delete(analysis)
        session.delete(idea)

    for analysis in session.exec(select(Analysis).where(Analysis.challenge_id == challenge_id)).all():
        session.delete(analysis)
    for gs in session.exec(select(GreenlightSession).where(GreenlightSession.challenge_id == challenge_id)).all():
        for approval in session.exec(select(SessionApproval).where(SessionApproval.session_id == gs.id)).all():
            session.delete(approval)
        session.delete(gs)
    for collab in session.exec(select(ChallengeCollaborator).where(ChallengeCollaborator.challenge_id == challenge_id)).all():
        session.delete(collab)

    session.delete(challenge)
    session.commit()
    return {"message": "Challenge permanently deleted"}


class AddCollaboratorRequest(PydanticBaseModel):
    email: str


@router.post("/{challenge_id}/collaborators")
def add_collaborator(
    challenge_id: int,
    data: AddCollaboratorRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    collab = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == challenge_id,
            ChallengeCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")

    target_user = session.exec(select(User).where(User.email == data.email)).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found with that email")

    existing = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == challenge_id,
            ChallengeCollaborator.user_id == target_user.id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a collaborator")

    new_collab = ChallengeCollaborator(
        challenge_id=challenge_id,
        user_id=target_user.id,
        role=CollaboratorRole.collaborator,
    )
    session.add(new_collab)
    session.commit()
    return {"message": f"Added {target_user.name} as collaborator"}
