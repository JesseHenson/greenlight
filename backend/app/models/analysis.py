from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class AnalysisType(str, Enum):
    pros_cons = "pros_cons"
    feasibility = "feasibility"
    impact = "impact"
    summary = "summary"


class Analysis(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    idea_id: int | None = Field(default=None, foreign_key="idea.id")
    challenge_id: int | None = Field(default=None, foreign_key="challenge.id")
    analysis_type: AnalysisType
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisRead(SQLModel):
    id: int
    idea_id: int | None
    challenge_id: int | None
    analysis_type: AnalysisType
    content: str
    created_at: datetime
