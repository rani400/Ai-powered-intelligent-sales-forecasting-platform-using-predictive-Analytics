"""SQLAlchemy ORM model for the ``company_insights`` table (Module 2: Lead Intelligence)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.lead import Lead


class CompanyInsight(Base):
    """A stored company analysis for a lead.

    Every run is persisted so that the generated insight can be audited and compared over time.
    """

    __tablename__ = "company_insights"

    insight_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leads.lead_id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    business_needs: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    opportunities: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    key_insights: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    information_gaps: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    qualification_score: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship(back_populates="insights")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CompanyInsight lead_id={self.lead_id} company={self.company_name!r}>"
