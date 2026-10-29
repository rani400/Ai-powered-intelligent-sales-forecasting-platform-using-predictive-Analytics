from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.intelligence import Factor


class ScoringRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    score_id: int
    lead_id: int
    score: float = Field(ge=0, le=100)
    priority_band: str
    factors: list[Factor]
    conversion_probability: float | None = Field(default=None, ge=0, le=1)
    prediction_mode: str
    model_version: str
    recommended_action: str
    recommendation_reason: str
    recommendation_priority: str
    supporting_factors: list[str]
    suggested_outreach_goal: str
    created_at: datetime


class ModelStatus(BaseModel):
    available: bool
    mode: str
    model_version: str
    metrics: dict | None
    notice: str
