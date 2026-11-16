"""Audit trail for CRM sync requests; never store provider tokens or full payloads."""
from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CRMSyncLog(Base):
    __tablename__ = 'crm_sync_logs'
    __table_args__ = (Index('ix_crm_sync_logs_lead_created', 'lead_id', 'created_at'),)
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.lead_id', ondelete='CASCADE'), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    remote_id: Mapped[str | None] = mapped_column(String(120))
    message: Mapped[str | None] = mapped_column(String(250))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
