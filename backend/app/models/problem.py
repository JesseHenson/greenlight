from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class ProblemStatus(str, Enum):
    active = "active"
    archived = "archived"


class CollaboratorRole(str, Enum):
    owner = "owner"
    collaborator = "collaborator"


class ProblemBase(SQLModel):
    title: str
    description: str


class Problem(ProblemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: ProblemStatus = Field(default=ProblemStatus.active)
    created_by: int = Field(foreign_key="user.id")
    group_id: int | None = Field(default=None, foreign_key="parentgroup.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProblemCollaborator(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.id")
    user_id: int = Field(foreign_key="user.id")
    role: CollaboratorRole = Field(default=CollaboratorRole.collaborator)


class ProblemCreate(SQLModel):
    title: str
    description: str
    group_id: int | None = None


class ProblemUpdate(SQLModel):
    title: str | None = None
    description: str | None = None


class ProblemRead(SQLModel):
    id: int
    title: str
    description: str
    status: ProblemStatus
    created_by: int
    created_at: datetime
    idea_count: int = 0
    session_status: str | None = None
