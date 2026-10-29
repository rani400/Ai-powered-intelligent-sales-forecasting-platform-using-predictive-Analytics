from datetime import datetime
from sqlalchemy import Integer, ForeignKey, Float, String, DateTime, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.lead import utcnow


class LeadScore(Base):
    __tablename__ = 'lead_scores'
    __table_args__ = (Index('ix_score_lead_date', 'lead_id', 'created_at'),)
    score_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.lead_id', ondelete='CASCADE'), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    priority_band: Mapped[str] = mapped_column(String(30), nullable=False)
    factors: Mapped[list] = mapped_column(JSON, nullable=False)
    conversion_probability: Mapped[float | None] = mapped_column(Float)
    prediction_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(200), nullable=False)
    recommendation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_priority: Mapped[str] = mapped_column(String(30), nullable=False)
    supporting_factors: Mapped[list] = mapped_column(JSON, nullable=False)
    suggested_outreach_goal: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    lead = relationship('Lead', back_populates='scores')
