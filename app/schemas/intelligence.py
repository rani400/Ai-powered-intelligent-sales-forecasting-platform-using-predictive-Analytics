from datetime import datetime
from pydantic import BaseModel, ConfigDict


class Factor(BaseModel):
    name: str
    points: float
    max_points: float
    explanation: str


class IntelligenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    insight_id: int
    lead_id: int
    company_summary: str
    industry_context: str
    potential_needs: list[str]
    potential_opportunities: list[str]
    observations: list[str]
    information_gaps: list[str]
    qualification_score: float
    qualification_band: str
    contributing_factors: list[Factor]
    methodology: str
    created_at: datetime
