from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.comment import Comment, CommentCreate, CommentRead
from app.models.idea import BrainstormIdea
from app.models.problem import ProblemCollaborator
from app.models.user import User

router = APIRouter(tags=["comments"])


def _check_collaborator(session, problem_id: int, user_id: int):
    collab = session.exec(
        select(ProblemCollaborator).where(
            ProblemCollaborator.problem_id == problem_id,
            ProblemCollaborator.user_id == user_id,
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
    idea = session.get(BrainstormIdea, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    _check_collaborator(session, idea.problem_id, current_user.id)

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
    idea = session.get(BrainstormIdea, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    _check_collaborator(session, idea.problem_id, current_user.id)

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
    return _enrich_comment(comment, session)
