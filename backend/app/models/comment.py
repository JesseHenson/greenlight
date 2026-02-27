from datetime import datetime

from sqlmodel import Field, SQLModel


class Comment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    idea_id: int = Field(foreign_key="brainstormidea.id", index=True)
    content: str
    created_by: int = Field(foreign_key="user.id")
    tone_flag: bool = Field(default=False)
    suggested_alternative: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CommentCreate(SQLModel):
    content: str
    tone_flag: bool = False
    suggested_alternative: str | None = None


class CommentRead(SQLModel):
    id: int
    idea_id: int
    content: str
    created_by: int
    creator_name: str | None = None
    tone_flag: bool
    suggested_alternative: str | None
    created_at: datetime
