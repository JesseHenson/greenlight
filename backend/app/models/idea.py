from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class IdeaStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"


class BrainstormIdea(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.id")
    content: str
    created_by: int = Field(foreign_key="user.id")
    status: IdeaStatus = Field(default=IdeaStatus.submitted)
    tone_flag: bool = Field(default=False)
    suggested_alternative: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IdeaCreate(SQLModel):
    content: str


class IdeaRead(SQLModel):
    id: int
    problem_id: int
    content: str
    created_by: int
    creator_name: str | None = None
    status: IdeaStatus
    tone_flag: bool
    suggested_alternative: str | None
    created_at: datetime
