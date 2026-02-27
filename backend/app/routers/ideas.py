from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.idea import BrainstormIdea, IdeaCreate, IdeaRead
from app.models.problem import ProblemCollaborator
from app.models.session import BrainstormSession, SessionStatus
from app.models.user import User

router = APIRouter(tags=["ideas"])


def _check_collaborator(session, problem_id: int, user_id: int):
    collab = session.exec(
        select(ProblemCollaborator).where(
            ProblemCollaborator.problem_id == problem_id,
            ProblemCollaborator.user_id == user_id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")


def _enrich_idea(idea: BrainstormIdea, session) -> IdeaRead:
    creator = session.get(User, idea.created_by)
    return IdeaRead(
        id=idea.id,
        problem_id=idea.problem_id,
        content=idea.content,
        created_by=idea.created_by,
        creator_name=creator.name if creator else None,
        status=idea.status,
        tone_flag=idea.tone_flag,
        suggested_alternative=idea.suggested_alternative,
        created_at=idea.created_at,
    )


@router.post("/api/problems/{problem_id}/ideas", response_model=IdeaRead)
def create_idea(
    problem_id: int,
    data: IdeaCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    _check_collaborator(session, problem_id, current_user.id)

    # Check session is in brainstorming phase
    bs = session.exec(
        select(BrainstormSession).where(BrainstormSession.problem_id == problem_id)
    ).first()
    if bs and bs.status != SessionStatus.brainstorming:
        raise HTTPException(
            status_code=400,
            detail="Brainstorming phase has ended. Cannot add new ideas.",
        )

    idea = BrainstormIdea(
        problem_id=problem_id,
        content=data.content,
        created_by=current_user.id,
    )
    session.add(idea)
    session.commit()
    session.refresh(idea)
    return _enrich_idea(idea, session)


@router.get("/api/problems/{problem_id}/ideas", response_model=list[IdeaRead])
def list_ideas(problem_id: int, session: SessionDep, current_user: CurrentUser):
    _check_collaborator(session, problem_id, current_user.id)
    ideas = session.exec(
        select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
    ).all()
    return [_enrich_idea(i, session) for i in ideas]


@router.patch("/api/ideas/{idea_id}", response_model=IdeaRead)
def update_idea(
    idea_id: int,
    data: IdeaCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    idea = session.get(BrainstormIdea, idea_id)
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
    return _enrich_idea(idea, session)


@router.delete("/api/ideas/{idea_id}")
def delete_idea(idea_id: int, session: SessionDep, current_user: CurrentUser):
    idea = session.get(BrainstormIdea, idea_id)
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

    session.delete(idea)
    session.commit()
    return {"message": "Idea deleted"}
