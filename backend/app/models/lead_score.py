"""SQLAlchemy ORM model for the ``lead_scores`` table (Module 4 baseline scoring)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.lead import Lead


class LeadScore(Base):
    """A point-in-time qualification score for a lead.

    One lead can accumulate many score rows, which preserves how the score evolved as the
    record was enriched.
    """

    __tablename__ = "lead_scores"

    score_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leads.lead_id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    band: Mapped[str] = mapped_column(String(20), nullable=False)
    factors: Mapped[str] = mapped_column(String(2000), nullable=False, default="[]")
    methodology: Mapped[str] = mapped_column(String(500), nullable=False, default="rule_based_v1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship(back_populates="scores")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<LeadScore lead_id={self.lead_id} score={self.score} band={self.band}>"
