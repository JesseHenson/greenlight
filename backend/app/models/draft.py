from datetime import datetime

from sqlmodel import Field, SQLModel, UniqueConstraint


class IdeaDraft(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("idea_id", "user_id"),)

    id: int | None = Field(default=None, primary_key=True)
    idea_id: int = Field(foreign_key="brainstormidea.id")
    user_id: int = Field(foreign_key="user.id")
    notes: str = Field(default="")
    want_pros_cons: bool = Field(default=False)
    want_feasibility: bool = Field(default=False)
    want_fairness: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IdeaDraftRead(SQLModel):
    id: int
    idea_id: int
    user_id: int
    notes: str
    want_pros_cons: bool
    want_feasibility: bool
    want_fairness: bool
    updated_at: datetime


class IdeaDraftUpdate(SQLModel):
    notes: str | None = None
    want_pros_cons: bool | None = None
    want_feasibility: bool | None = None
    want_fairness: bool | None = None
