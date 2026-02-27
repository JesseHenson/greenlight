from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class SessionStatus(str, Enum):
    brainstorming = "brainstorming"
    approved_for_analysis = "approved_for_analysis"
    analysis_in_progress = "analysis_in_progress"
    analysis_complete = "analysis_complete"


class BrainstormSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.id", unique=True)
    status: SessionStatus = Field(default=SessionStatus.brainstorming)
    approved_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionRead(SQLModel):
    id: int
    problem_id: int
    status: SessionStatus
    approved_at: datetime | None
    created_at: datetime
    approvals: list[dict] = []
    total_collaborators: int = 0
    all_approved: bool = False
