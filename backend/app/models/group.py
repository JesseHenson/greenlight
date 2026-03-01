from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel, UniqueConstraint


class GroupRole(str, Enum):
    owner = "owner"
    member = "member"


class Team(SQLModel, table=True):
    __tablename__ = "team"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TeamMember(SQLModel, table=True):
    __tablename__ = "teammember"
    __table_args__ = (UniqueConstraint("group_id", "user_id"),)

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="team.id")
    user_id: int = Field(foreign_key="user.id")
    role: GroupRole = Field(default=GroupRole.member)
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class PendingTeamInvite(SQLModel, table=True):
    __tablename__ = "pendingteaminvite"

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="team.id")
    email: str = Field(index=True)
    invited_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TeamRead(SQLModel):
    id: int
    name: str
    members: list[dict] = []
