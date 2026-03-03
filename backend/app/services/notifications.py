"""Create in-app notifications for collaborators."""

import logging

from sqlmodel import Session, select

from app.models.notification import Notification, NotificationType
from app.models.problem import ChallengeCollaborator
from app.models.user import User

logger = logging.getLogger(__name__)


def notify_collaborators(
    session: Session,
    challenge_id: int,
    sender_id: int,
    notification_type: NotificationType,
    title: str,
    body: str,
):
    """Create a notification for every collaborator except the sender."""
    collabs = session.exec(
        select(ChallengeCollaborator).where(
            ChallengeCollaborator.challenge_id == challenge_id
        )
    ).all()
    for collab in collabs:
        if collab.user_id == sender_id:
            continue
        session.add(Notification(
            user_id=collab.user_id,
            type=notification_type,
            title=title,
            body=body,
            challenge_id=challenge_id,
        ))
    session.commit()


def notify_user(
    session: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    body: str,
    challenge_id: int | None = None,
):
    """Create a notification for a single user."""
    session.add(Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        challenge_id=challenge_id,
    ))
    session.commit()
