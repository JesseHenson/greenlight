import asyncio

import sentry_sdk
from sqlmodel import Session, select

from app.ai.analyzer import analyze_idea
from app.ai.summarizer import summarize_session
from app.database import engine
from app.models.analysis import Analysis, AnalysisType
from app.models.idea import Idea
from app.models.problem import Challenge, ChallengeCollaborator
from app.models.session import GreenlightSession, SessionStatus
from app.models.user import User


def run_analysis(challenge_id: int):
    """Run full analysis pipeline as a background task."""
    asyncio.run(_run_analysis_async(challenge_id))


async def _run_analysis_async(challenge_id: int):
    with Session(engine) as session:
        # Update session status
        gs = session.exec(
            select(GreenlightSession).where(GreenlightSession.challenge_id == challenge_id)
        ).first()
        if not gs:
            return
        gs.status = SessionStatus.analysis_in_progress
        session.add(gs)
        session.commit()

        challenge = session.get(Challenge, challenge_id)
        ideas = session.exec(
            select(Idea).where(Idea.challenge_id == challenge_id)
        ).all()

        challenge_context = f"{challenge.title}: {challenge.description}"

        # Analyze each idea with all 3 types
        for idea in ideas:
            for atype in [AnalysisType.pros_cons, AnalysisType.feasibility, AnalysisType.impact]:
                try:
                    content = await analyze_idea(idea.content, challenge_context, atype.value)
                    analysis = Analysis(
                        idea_id=idea.id,
                        analysis_type=atype,
                        content=content,
                    )
                    session.add(analysis)
                    session.commit()
                except Exception as e:
                    sentry_sdk.capture_exception(e)

        # Generate session summary
        ideas_text_parts = []
        for idea in ideas:
            analyses = session.exec(
                select(Analysis).where(Analysis.idea_id == idea.id)
            ).all()
            analyses_text = "\n".join(
                f"  [{a.analysis_type}]: {a.content}" for a in analyses
            )
            ideas_text_parts.append(f"Idea: {idea.content}\n{analyses_text}")

        ideas_with_analyses = "\n\n".join(ideas_text_parts)

        try:
            summary_content = await summarize_session(
                challenge.title, challenge.description, ideas_with_analyses
            )
            summary = Analysis(
                challenge_id=challenge_id,
                analysis_type=AnalysisType.summary,
                content=summary_content,
            )
            session.add(summary)
        except Exception as e:
            sentry_sdk.capture_exception(e)

        # Mark complete
        gs.status = SessionStatus.analysis_complete
        session.add(gs)
        session.commit()

        # Broadcast real-time update
        from app.services.sse import broadcast
        broadcast(challenge_id, "analysis_complete")

        # Notify collaborators via email + in-app
        try:
            from app.config import settings
            from app.services.email import send_analysis_complete_email
            from app.models.notification import Notification, NotificationType

            collabs = session.exec(
                select(ChallengeCollaborator).where(
                    ChallengeCollaborator.challenge_id == challenge_id
                )
            ).all()
            for collab in collabs:
                user = session.get(User, collab.user_id)
                if user:
                    # In-app notification
                    session.add(Notification(
                        user_id=user.id,
                        type=NotificationType.analysis_complete,
                        title="Analysis complete",
                        body=f"AI analysis for \"{challenge.title}\" is ready to review",
                        challenge_id=challenge_id,
                    ))
                    # Email notification
                    if user.email:
                        send_analysis_complete_email(
                            to_email=user.email,
                            user_name=user.name,
                            challenge_title=challenge.title,
                            app_url=settings.app_url,
                            challenge_id=challenge_id,
                        )
            session.commit()
        except Exception as e:
            sentry_sdk.capture_exception(e)
