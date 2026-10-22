"""SQLAlchemy ORM model for the ``outreach_campaigns`` table (Module 3: AI Outreach)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.lead import Lead


class CampaignStatus:
    """Lifecycle states for a stored outreach campaign."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    FAILED = "failed"


class OutreachCampaign(Base):
    """A stored email draft produced for a lead.

    A draft is only ever written with ``campaign_status = 'draft'`` in this scope: there is no
    sending workflow, so nothing may be marked as sent.
    """

    __tablename__ = "outreach_campaigns"

    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leads.lead_id", ondelete="CASCADE"), nullable=False, index=True
    )
    email_subject: Mapped[str] = mapped_column(String(300), nullable=False)
    email_content: Mapped[str] = mapped_column(Text, nullable=False)
    campaign_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=CampaignStatus.DRAFT, index=True
    )
    tone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email_length: Mapped[str | None] = mapped_column(String(40), nullable=True)
    communication_goal: Mapped[str | None] = mapped_column(String(60), nullable=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="mock")
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    generation_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship(back_populates="campaigns")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<OutreachCampaign id={self.campaign_id} lead_id={self.lead_id} status={self.campaign_status}>"
