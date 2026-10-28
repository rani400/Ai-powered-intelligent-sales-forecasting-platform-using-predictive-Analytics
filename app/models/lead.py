from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Lead(Base):
    __tablename__ = 'leads'
    __table_args__ = (
        CheckConstraint('engagement_score >= 0 AND engagement_score <= 100', name='ck_lead_engagement'),
        Index('ix_leads_company_contact', 'company_name', 'contact_name'),
    )
    lead_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(100), index=True)
    contact_name: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(254), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    lead_status: Mapped[str] = mapped_column(String(30), nullable=False, default='New', index=True)
    company_size: Mapped[str | None] = mapped_column(String(30))
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    insights = relationship('CompanyInsight', back_populates='lead', cascade='all, delete-orphan', passive_deletes=True)
    scores = relationship('LeadScore', back_populates='lead', cascade='all, delete-orphan', passive_deletes=True)
    campaigns = relationship('OutreachCampaign', back_populates='lead', cascade='all, delete-orphan', passive_deletes=True)
