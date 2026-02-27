from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class AnalysisType(str, Enum):
    pros_cons = "pros_cons"
    feasibility = "feasibility"
    fairness = "fairness"
    summary = "summary"


class Analysis(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    brainstorm_idea_id: int | None = Field(default=None, foreign_key="brainstormidea.id")
    problem_id: int | None = Field(default=None, foreign_key="problem.id")
    analysis_type: AnalysisType
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisRead(SQLModel):
    id: int
    brainstorm_idea_id: int | None
    problem_id: int | None
    analysis_type: AnalysisType
    content: str
    created_at: datetime
