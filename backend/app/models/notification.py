from datetime import datetime, UTC
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class NotificationType(str, Enum):
    idea_added = "idea_added"
    comment_added = "comment_added"
    approval_changed = "approval_changed"
    analysis_complete = "analysis_complete"
    team_invite = "team_invite"


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    type: NotificationType
    title: str
    body: str
    challenge_id: Optional[int] = Field(default=None, foreign_key="challenge.id")
    read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NotificationRead(SQLModel):
    id: int
    type: NotificationType
    title: str
    body: str
    challenge_id: Optional[int]
    read: bool
    created_at: datetime
