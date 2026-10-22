"""SQLAlchemy ORM model for the ``leads`` table (Module 1: Lead Management)."""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.company_insight import CompanyInsight
    from app.models.lead_score import LeadScore
    from app.models.outreach_campaign import OutreachCampaign


class LeadStatus(str, enum.Enum):
    """Canonical lifecycle states for a prospect record."""

    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    UNQUALIFIED = "Unqualified"
    CONVERTED = "Converted"
    LOST = "Lost"


class LeadSource(str, enum.Enum):
    """How the record entered the system."""

    MANUAL = "manual"
    CSV_IMPORT = "csv_import"


class Lead(Base):
    """A prospect company together with its primary contact."""

    __tablename__ = "leads"

    lead_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    lead_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=LeadStatus.NEW.value, index=True
    )
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default=LeadSource.MANUAL.value)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    scores: Mapped[list["LeadScore"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    insights: Mapped[list["CompanyInsight"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    campaigns: Mapped[list["OutreachCampaign"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Lead id={self.lead_id} company={self.company_name!r} email={self.email!r}>"
