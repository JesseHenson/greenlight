from fastmcp import FastMCP
from sqlmodel import Session, select

from app.database import engine
from app.models.analysis import Analysis, AnalysisType
from app.models.idea import BrainstormIdea
from app.models.problem import Problem
from app.models.session import BrainstormSession

mcp = FastMCP("CommonGround")


@mcp.tool()
def get_problem_context(problem_id: int) -> dict:
    """Get full details about a co-parenting problem."""
    with Session(engine) as session:
        problem = session.get(Problem, problem_id)
        if not problem:
            return {"error": "Problem not found"}
        bs = session.exec(
            select(BrainstormSession).where(BrainstormSession.problem_id == problem_id)
        ).first()
        return {
            "id": problem.id,
            "title": problem.title,
            "description": problem.description,
            "status": problem.status,
            "session_status": bs.status if bs else None,
        }


@mcp.tool()
def get_all_ideas(problem_id: int) -> list[dict]:
    """Get all brainstorm ideas for a problem."""
    with Session(engine) as session:
        ideas = session.exec(
            select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
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
def get_brainstorm_status(problem_id: int) -> dict:
    """Get the current brainstorm session status."""
    with Session(engine) as session:
        bs = session.exec(
            select(BrainstormSession).where(BrainstormSession.problem_id == problem_id)
        ).first()
        if not bs:
            return {"error": "No session found"}
        ideas = session.exec(
            select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
        ).all()
        return {
            "status": bs.status,
            "idea_count": len(ideas),
            "approved_at": str(bs.approved_at) if bs.approved_at else None,
        }


@mcp.tool()
def submit_analysis(idea_id: int, analysis_type: str, content: str) -> dict:
    """Submit an analysis for a brainstorm idea. Type must be: pros_cons, feasibility, or fairness."""
    if analysis_type not in ["pros_cons", "feasibility", "fairness"]:
        return {"error": "Invalid analysis type"}
    with Session(engine) as session:
        idea = session.get(BrainstormIdea, idea_id)
        if not idea:
            return {"error": "Idea not found"}
        analysis = Analysis(
            brainstorm_idea_id=idea_id,
            analysis_type=AnalysisType(analysis_type),
            content=content,
        )
        session.add(analysis)
        session.commit()
        return {"id": analysis.id, "status": "created"}


if __name__ == "__main__":
    mcp.run()
