from datetime import datetime

from sqlmodel import Field, SQLModel, UniqueConstraint


class SessionApproval(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("session_id", "user_id"),)

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="brainstormsession.id")
    user_id: int = Field(foreign_key="user.id")
    approved_at: datetime = Field(default_factory=datetime.utcnow)


class SessionApprovalRead(SQLModel):
    id: int
    session_id: int
    user_id: int
    user_name: str
    approved_at: datetime
