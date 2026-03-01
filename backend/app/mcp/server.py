from fastmcp import FastMCP
from sqlmodel import Session, select

from app.database import engine
from app.models.analysis import Analysis, AnalysisType
from app.models.idea import Idea
from app.models.problem import Challenge
from app.models.session import GreenlightSession

mcp = FastMCP("Greenlight")


@mcp.tool()
def get_challenge_context(challenge_id: int) -> dict:
    """Get full details about a brainstorming challenge."""
    with Session(engine) as session:
        challenge = session.get(Challenge, challenge_id)
        if not challenge:
            return {"error": "Challenge not found"}
        gs = session.exec(
            select(GreenlightSession).where(GreenlightSession.challenge_id == challenge_id)
        ).first()
        return {
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "status": challenge.status,
            "session_status": gs.status if gs else None,
        }


@mcp.tool()
def get_all_ideas(challenge_id: int) -> list[dict]:
    """Get all ideas for a challenge."""
    with Session(engine) as session:
        ideas = session.exec(
            select(Idea).where(Idea.challenge_id == challenge_id)
        ).all()
        return [
            {
                "id": i.id,
                "content": i.content,
                "tone_flag": i.tone_flag,
                "created_at": str(i.created_at),
            }
            for i in ideas
        ]


@mcp.tool()
def get_session_status(challenge_id: int) -> dict:
    """Get the current greenlight session status."""
    with Session(engine) as session:
        gs = session.exec(
            select(GreenlightSession).where(GreenlightSession.challenge_id == challenge_id)
        ).first()
        if not gs:
            return {"error": "No session found"}
        ideas = session.exec(
            select(Idea).where(Idea.challenge_id == challenge_id)
        ).all()
        return {
            "status": gs.status,
            "idea_count": len(ideas),
            "approved_at": str(gs.approved_at) if gs.approved_at else None,
        }


@mcp.tool()
def submit_analysis(idea_id: int, analysis_type: str, content: str) -> dict:
    """Submit an analysis for an idea. Type must be: pros_cons, feasibility, or impact."""
    if analysis_type not in ["pros_cons", "feasibility", "impact"]:
        return {"error": "Invalid analysis type"}
    with Session(engine) as session:
        idea = session.get(Idea, idea_id)
        if not idea:
            return {"error": "Idea not found"}
        analysis = Analysis(
            idea_id=idea_id,
            analysis_type=AnalysisType(analysis_type),
            content=content,
        )
        session.add(analysis)
        session.commit()
        return {"id": analysis.id, "status": "created"}


if __name__ == "__main__":
    mcp.run()
