from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class ChallengeStatus(str, Enum):
    active = "active"
    archived = "archived"


class CollaboratorRole(str, Enum):
    owner = "owner"
    collaborator = "collaborator"


class ChallengeBase(SQLModel):
    title: str
    description: str


class Challenge(ChallengeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: ChallengeStatus = Field(default=ChallengeStatus.active)
    created_by: int = Field(foreign_key="user.id")
    group_id: int | None = Field(default=None, foreign_key="team.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChallengeCollaborator(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    challenge_id: int = Field(foreign_key="challenge.id")
    user_id: int = Field(foreign_key="user.id")
    role: CollaboratorRole = Field(default=CollaboratorRole.collaborator)


class ChallengeCreate(SQLModel):
    title: str
    description: str
    group_id: int | None = None


class ChallengeUpdate(SQLModel):
    title: str | None = None
    description: str | None = None


class ChallengeRead(SQLModel):
    id: int
    title: str
    description: str
    status: ChallengeStatus
    created_by: int
    created_at: datetime
    idea_count: int = 0
    session_status: str | None = None
