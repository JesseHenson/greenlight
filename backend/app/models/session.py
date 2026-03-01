from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class SessionStatus(str, Enum):
    ideate = "ideate"
    build = "build"
    approved_for_analysis = "approved_for_analysis"
    analysis_in_progress = "analysis_in_progress"
    analysis_complete = "analysis_complete"


class GreenlightSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    challenge_id: int = Field(foreign_key="challenge.id", unique=True)
    status: SessionStatus = Field(default=SessionStatus.ideate)
    approved_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionRead(SQLModel):
    id: int
    challenge_id: int
    status: SessionStatus
    approved_at: datetime | None
    created_at: datetime
    approvals: list[dict] = []
    total_collaborators: int = 0
    all_approved: bool = False
