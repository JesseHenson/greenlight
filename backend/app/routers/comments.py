from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.comment import Comment, CommentCreate, CommentRead
from app.models.idea import Idea
from app.models.problem import ChallengeCollaborator
from app.models.user import User

router = APIRouter(tags=["comments"])


def _check_collaborator(session, challenge_id: int, user_id: int):
    collab = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == challenge_id,
            ChallengeCollaborator.user_id == user_id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")


def _enrich_comment(comment: Comment, session) -> CommentRead:
    creator = session.get(User, comment.created_by)
    return CommentRead(
        id=comment.id,
        idea_id=comment.idea_id,
        content=comment.content,
        created_by=comment.created_by,
        creator_name=creator.name if creator else None,
        tone_flag=comment.tone_flag,
        suggested_alternative=comment.suggested_alternative,
        created_at=comment.created_at,
    )


@router.get("/api/ideas/{idea_id}/comments", response_model=list[CommentRead])
def list_comments(idea_id: int, session: SessionDep, current_user: CurrentUser):
    idea = session.get(Idea, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    _check_collaborator(session, idea.challenge_id, current_user.id)

    comments = session.exec(
        select(Comment)
        .where(Comment.idea_id == idea_id)
        .order_by(Comment.created_at.asc())
    ).all()
    return [_enrich_comment(c, session) for c in comments]


@router.post("/api/ideas/{idea_id}/comments", response_model=CommentRead)
def create_comment(
    idea_id: int,
    data: CommentCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    idea = session.get(Idea, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    _check_collaborator(session, idea.challenge_id, current_user.id)

    comment = Comment(
        idea_id=idea_id,
        content=data.content,
        created_by=current_user.id,
        tone_flag=data.tone_flag,
        suggested_alternative=data.suggested_alternative,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)

    from app.services.notifications import notify_collaborators
    from app.models.notification import NotificationType
    preview = data.content[:80] + ("..." if len(data.content) > 80 else "")
    notify_collaborators(
        session, idea.challenge_id, current_user.id,
        NotificationType.comment_added,
        f"{current_user.name} commented",
        preview,
    )

    return _enrich_comment(comment, session)
