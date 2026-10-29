from datetime import datetime
from sqlalchemy import Integer, ForeignKey, Text, String, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.lead import utcnow


class OutreachCampaign(Base):
    __tablename__ = 'outreach_campaigns'
    __table_args__ = (Index('ix_campaign_lead_date', 'lead_id', 'created_at'),)
    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.lead_id', ondelete='CASCADE'), nullable=False, index=True)
    email_subject: Mapped[str] = mapped_column(String(300), nullable=False)
    email_content: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(String(30), nullable=False)
    communication_goal: Mapped[str] = mapped_column(String(40), nullable=False)
    email_length: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False)
    campaign_status: Mapped[str] = mapped_column(String(20), default='DRAFT', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    lead = relationship('Lead', back_populates='campaigns')
