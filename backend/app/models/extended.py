"""Tables designed for later milestones (Module 5 and Module 6).

These models exist so the database design is complete and the relationships from the project
diagram are real, but **no business logic is implemented for them in this scope**. The services
and endpoints for conversation intelligence, CRM synchronisation and full sales analytics are
later-stage work.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.lead import Lead


class InteractionType(str, enum.Enum):
    """Kinds of recorded sales interaction."""

    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"


class CRMSyncStatus(str, enum.Enum):
    """Outcome of a CRM synchronisation attempt."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class User(Base):
    """A platform user (Module 5)."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="sales_rep")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User id={self.user_id} email={self.email!r}>"


class SalesInteraction(Base):
    """A recorded interaction with a lead (Module 5: conversation intelligence)."""

    __tablename__ = "sales_interactions"

    interaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leads.lead_id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    interaction_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default=InteractionType.NOTE.value
    )
    subject: Mapped[str | None] = mapped_column(String(300), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SalesInteraction id={self.interaction_id} lead_id={self.lead_id}>"


class CRMSyncLog(Base):
    """Audit trail for CRM synchronisation (Module 5)."""

    __tablename__ = "crm_sync_logs"

    sync_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("leads.lead_id", ondelete="SET NULL"), nullable=True, index=True
    )
    crm_system: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False, default="lead")
    sync_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=CRMSyncStatus.PENDING.value
    )
    records_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CRMSyncLog id={self.sync_id} status={self.sync_status}>"


class SalesAnalyticsSnapshot(Base):
    """A pre-aggregated analytics snapshot (Module 6)."""

    __tablename__ = "sales_analytics"

    snapshot_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_leads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qualified_leads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    converted_leads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_lead_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SalesAnalyticsSnapshot id={self.snapshot_id}>"
