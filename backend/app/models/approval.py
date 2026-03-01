from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel, UniqueConstraint


class GateType(str, Enum):
    ideate_to_build = "ideate_to_build"
    build_to_converge = "build_to_converge"


class SessionApproval(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("session_id", "user_id", "gate"),)

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="greenlightsession.id")
    user_id: int = Field(foreign_key="user.id")
    gate: GateType
    approved_at: datetime = Field(default_factory=datetime.utcnow)


class SessionApprovalRead(SQLModel):
    id: int
    session_id: int
    user_id: int
    user_name: str
    gate: GateType
    approved_at: datetime
