from datetime import datetime
from sqlalchemy import Integer, ForeignKey, Text, JSON, Float, String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.lead import utcnow


class CompanyInsight(Base):
    __tablename__ = 'company_insights'
    __table_args__ = (Index('ix_insight_lead_date', 'lead_id', 'created_at'),)
    insight_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.lead_id', ondelete='CASCADE'), nullable=False, index=True)
    company_summary: Mapped[str] = mapped_column(Text, nullable=False)
    industry_context: Mapped[str] = mapped_column(Text, nullable=False)
    potential_needs: Mapped[list] = mapped_column(JSON, nullable=False)
    potential_opportunities: Mapped[list] = mapped_column(JSON, nullable=False)
    observations: Mapped[list] = mapped_column(JSON, nullable=False)
    information_gaps: Mapped[list] = mapped_column(JSON, nullable=False)
    qualification_score: Mapped[float] = mapped_column(Float, nullable=False)
    qualification_band: Mapped[str] = mapped_column(String(30), nullable=False)
    contributing_factors: Mapped[list] = mapped_column(JSON, nullable=False)
    methodology: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    lead = relationship('Lead', back_populates='insights')
