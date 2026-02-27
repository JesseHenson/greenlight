from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.idea import BrainstormIdea
from app.models.problem import Problem, ProblemCollaborator

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ToneCheckRequest(BaseModel):
    content: str


class ToneCheckResponse(BaseModel):
    is_hostile: bool
    reason: str
    suggested_alternative: str


@router.post("/check-tone", response_model=ToneCheckResponse)
async def check_tone(data: ToneCheckRequest):
    from app.ai.mediator import check_tone

    result = await check_tone(data.content)
    return result


class SuggestionResponse(BaseModel):
    suggestions: list[dict]


@router.post("/suggest-ideas/{problem_id}", response_model=SuggestionResponse)
async def suggest_ideas(
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

    problem = session.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    existing_ideas = session.exec(
        select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
    ).all()

    from app.ai.suggester import suggest_ideas

    suggestions = await suggest_ideas(problem, [i.content for i in existing_ideas])
    return {"suggestions": suggestions}
