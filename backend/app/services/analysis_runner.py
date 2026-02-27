import asyncio

from sqlmodel import Session, select

from app.ai.analyzer import analyze_idea
from app.ai.summarizer import summarize_session
from app.database import engine
from app.models.analysis import Analysis, AnalysisType
from app.models.idea import BrainstormIdea
from app.models.problem import Problem
from app.models.session import BrainstormSession, SessionStatus


def run_analysis(problem_id: int):
    """Run full analysis pipeline as a background task."""
    asyncio.run(_run_analysis_async(problem_id))


async def _run_analysis_async(problem_id: int):
    with Session(engine) as session:
        # Update session status
        bs = session.exec(
            select(BrainstormSession).where(BrainstormSession.problem_id == problem_id)
        ).first()
        if not bs:
            return
        bs.status = SessionStatus.analysis_in_progress
        session.add(bs)
        session.commit()

        problem = session.get(Problem, problem_id)
        ideas = session.exec(
            select(BrainstormIdea).where(BrainstormIdea.problem_id == problem_id)
        ).all()

        problem_context = f"{problem.title}: {problem.description}"

        # Analyze each idea with all 3 types
        for idea in ideas:
            for atype in [AnalysisType.pros_cons, AnalysisType.feasibility, AnalysisType.fairness]:
                try:
                    content = await analyze_idea(idea.content, problem_context, atype.value)
                    analysis = Analysis(
                        brainstorm_idea_id=idea.id,
                        analysis_type=atype,
                        content=content,
                    )
                    session.add(analysis)
                    session.commit()
                except Exception as e:
                    print(f"Error analyzing idea {idea.id} ({atype}): {e}")

        # Generate session summary
        ideas_text_parts = []
        for idea in ideas:
            analyses = session.exec(
                select(Analysis).where(Analysis.brainstorm_idea_id == idea.id)
            ).all()
            analyses_text = "\n".join(
                f"  [{a.analysis_type}]: {a.content}" for a in analyses
            )
            ideas_text_parts.append(f"Idea: {idea.content}\n{analyses_text}")

        ideas_with_analyses = "\n\n".join(ideas_text_parts)

        try:
            summary_content = await summarize_session(
                problem.title, problem.description, ideas_with_analyses
            )
            summary = Analysis(
                problem_id=problem_id,
                analysis_type=AnalysisType.summary,
                content=summary_content,
            )
            session.add(summary)
        except Exception as e:
            print(f"Error generating summary: {e}")

        # Mark complete
        bs.status = SessionStatus.analysis_complete
        session.add(bs)
        session.commit()
