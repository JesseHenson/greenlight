from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.problem import (
    Problem,
    ProblemCollaborator,
    ProblemCreate,
    ProblemRead,
    ProblemUpdate,
    ProblemStatus,
    CollaboratorRole,
)
from app.models.session import BrainstormSession, SessionStatus
from app.models.idea import BrainstormIdea
from app.models.user import User
from app.models.group import ParentGroupMember

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.post("", response_model=ProblemRead)
def create_problem(data: ProblemCreate, session: SessionDep, current_user: CurrentUser):
    problem = Problem(
        title=data.title,
        description=data.description,
        created_by=current_user.id,
        group_id=data.group_id,
    )
    session.add(problem)
    session.commit()
    session.refresh(problem)

    # Auto-add owner as collaborator
    collab = ProblemCollaborator(
        problem_id=problem.id,
        user_id=current_user.id,
        role=CollaboratorRole.owner,
    )
    session.add(collab)

    # If group_id provided, auto-add all group members as collaborators
    if data.group_id:
        group_members = session.exec(
            select(ParentGroupMember).where(ParentGroupMember.group_id == data.group_id)
        ).all()
        for gm in group_members:
            if gm.user_id != current_user.id:
                session.add(ProblemCollaborator(
                    problem_id=problem.id,
                    user_id=gm.user_id,
                    role=CollaboratorRole.collaborator,
                ))

    # Auto-create brainstorm session
    bs = BrainstormSession(problem_id=problem.id)
    session.add(bs)
    session.commit()

    return ProblemRead(
        id=problem.id,
        title=problem.title,
        description=problem.description,
        status=problem.status,
        created_by=problem.created_by,
        created_at=problem.created_at,
        idea_count=0,
        session_status=bs.status,
    )


@router.get("", response_model=list[ProblemRead])
def list_problems(session: SessionDep, current_user: CurrentUser):
    # Get active problems where user is a collaborator
    stmt = (
        select(Problem)
        .join(ProblemCollaborator, ProblemCollaborator.problem_id == Problem.id)
        .where(
            ProblemCollaborator.user_id == current_user.id,
            Problem.status == ProblemStatus.active,
        )
    )
    problems = session.exec(stmt).all()
    result = []
    for p in problems:
        idea_count = len(
            session.exec(
                select(BrainstormIdea).where(BrainstormIdea.problem_id == p.id)
            ).all()
        )
        bs = session.exec(
            select(BrainstormSession).where(BrainstormSession.problem_id == p.id)
        ).first()
        result.append(
            ProblemRead(
                id=p.id,
                title=p.title,
                description=p.description,
                status=p.status,
                created_by=p.created_by,
                created_at=p.created_at,
                idea_count=idea_count,
                session_status=bs.status if bs else None,
            )
        )
    return result


@router.get("/{problem_id}", response_model=ProblemRead)
def get_problem(problem_id: int, session: SessionDep, current_user: CurrentUser):
    problem = session.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    # Check user is collaborator
    collab = session.exec(
        select(ProblemCollaborator).where(
            ProblemCollaborator.problem_id == problem_id,
            ProblemCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator on this problem")

    idea_count = len(
        session.exec(
            select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
        ).all()
    )
    bs = session.exec(
        select(BrainstormSession).where(BrainstormSession.problem_id == problem_id)
    ).first()

    return ProblemRead(
        id=problem.id,
        title=problem.title,
        description=problem.description,
        status=problem.status,
        created_by=problem.created_by,
        created_at=problem.created_at,
        idea_count=idea_count,
        session_status=bs.status if bs else None,
    )


@router.patch("/{problem_id}", response_model=ProblemRead)
def update_problem(
    problem_id: int,
    data: ProblemUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    problem = session.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can edit")

    if data.title is not None:
        problem.title = data.title
    if data.description is not None:
        problem.description = data.description
    session.add(problem)
    session.commit()
    session.refresh(problem)

    idea_count = len(
        session.exec(
            select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
        ).all()
    )
    bs = session.exec(
        select(BrainstormSession).where(BrainstormSession.problem_id == problem_id)
    ).first()

    return ProblemRead(
        id=problem.id,
        title=problem.title,
        description=problem.description,
        status=problem.status,
        created_by=problem.created_by,
        created_at=problem.created_at,
        idea_count=idea_count,
        session_status=bs.status if bs else None,
    )


@router.post("/{problem_id}/archive")
def archive_problem(problem_id: int, session: SessionDep, current_user: CurrentUser):
    problem = session.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can archive")
    problem.status = ProblemStatus.archived
    session.add(problem)
    session.commit()
    return {"message": "Conversation archived"}


from pydantic import BaseModel as PydanticBaseModel


class DeleteRequest(PydanticBaseModel):
    password: str


DELETE_PASSWORD = "confirm-delete"


@router.post("/{problem_id}/delete")
def delete_problem(
    problem_id: int,
    data: DeleteRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    problem = session.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can delete")
    if data.password != DELETE_PASSWORD:
        raise HTTPException(status_code=403, detail="Incorrect delete password")

    from app.models.comment import Comment
    from app.models.analysis import Analysis
    from app.models.draft import IdeaDraft
    from app.models.approval import SessionApproval

    ideas = session.exec(
        select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
    ).all()
    for idea in ideas:
        for draft in session.exec(select(IdeaDraft).where(IdeaDraft.idea_id == idea.id)).all():
            session.delete(draft)
        for comment in session.exec(select(Comment).where(Comment.idea_id == idea.id)).all():
            session.delete(comment)
        for analysis in session.exec(select(Analysis).where(Analysis.brainstorm_idea_id == idea.id)).all():
            session.delete(analysis)
        session.delete(idea)

    for analysis in session.exec(select(Analysis).where(Analysis.problem_id == problem_id)).all():
        session.delete(analysis)
    for bs in session.exec(select(BrainstormSession).where(BrainstormSession.problem_id == problem_id)).all():
        for approval in session.exec(select(SessionApproval).where(SessionApproval.session_id == bs.id)).all():
            session.delete(approval)
        session.delete(bs)
    for collab in session.exec(select(ProblemCollaborator).where(ProblemCollaborator.problem_id == problem_id)).all():
        session.delete(collab)

    session.delete(problem)
    session.commit()
    return {"message": "Problem permanently deleted"}


class AddCollaboratorRequest(PydanticBaseModel):
    email: str


@router.post("/{problem_id}/collaborators")
def add_collaborator(
    problem_id: int,
    data: AddCollaboratorRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    problem = session.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Check requesting user is a collaborator
    collab = session.exec(
        select(ProblemCollaborator).where(
            ProblemCollaborator.problem_id == problem_id,
            ProblemCollaborator.user_id == current_user.id,
        )
    ).first()
    if not collab:
        raise HTTPException(status_code=403, detail="Not a collaborator")

    # Find user by email
    target_user = session.exec(select(User).where(User.email == data.email)).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found with that email")

    # Check not already a collaborator
    existing = session.exec(
        select(ProblemCollaborator).where(
            ProblemCollaborator.problem_id == problem_id,
            ProblemCollaborator.user_id == target_user.id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a collaborator")

    new_collab = ProblemCollaborator(
        problem_id=problem_id,
        user_id=target_user.id,
        role=CollaboratorRole.collaborator,
    )
    session.add(new_collab)
    session.commit()
    return {"message": f"Added {target_user.name} as collaborator"}
