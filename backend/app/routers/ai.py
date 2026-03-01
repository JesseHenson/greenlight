from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.idea import Idea
from app.models.problem import Challenge, ChallengeCollaborator
from app.models.session import GreenlightSession

router = APIRouter(prefix="/api/ai", tags=["ai"])


class CreativityCheckRequest(BaseModel):
    content: str
    stage: str = "ideate"


class CreativityCheckResponse(BaseModel):
    is_convergent: bool
    reason: str
    suggested_alternative: str


@router.post("/check-creativity", response_model=CreativityCheckResponse)
async def check_creativity(data: CreativityCheckRequest):
    from app.ai.mediator import check_creativity

    result = await check_creativity(data.content, data.stage)
    return result


class SuggestionResponse(BaseModel):
    suggestions: list[dict]


@router.post("/suggest-ideas/{challenge_id}", response_model=SuggestionResponse)
async def suggest_ideas(
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

    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    existing_ideas = session.exec(
        select(Idea).where(Idea.challenge_id == challenge_id)
    ).all()

    from app.ai.suggester import suggest_ideas

    suggestions = await suggest_ideas(challenge, [i.content for i in existing_ideas])
    return {"suggestions": suggestions}
