"""Request and response schemas for the AI outreach generation endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OutreachRequest(BaseModel):
    """Request body for ``POST /api/outreach/generate``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: int = Field(..., gt=0, description="Identifier of the lead to write to")
    company_name: str | None = Field(default=None, max_length=200)
    contact_name: str | None = Field(default=None, max_length=120)
    industry: str | None = Field(default=None, max_length=120)
    product_or_service: str = Field(..., min_length=1, max_length=300)
    communication_goal: str = Field(default="product_introduction", max_length=60)
    tone: str = Field(default="professional", max_length=40)
    email_length: str = Field(default="short", max_length=40)

    @field_validator("communication_goal")
    @classmethod
    def _validate_goal(cls, value: str) -> str:
        allowed = {"product_introduction", "meeting", "follow_up"}
        candidate = value.strip().lower()
        if candidate not in allowed:
            raise ValueError("must be one of: " + ", ".join(sorted(allowed)))
        return candidate

    @field_validator("tone")
    @classmethod
    def _validate_tone(cls, value: str) -> str:
        allowed = {"professional", "friendly"}
        candidate = value.strip().lower()
        if candidate not in allowed:
            raise ValueError("must be one of: " + ", ".join(sorted(allowed)))
        return candidate

    @field_validator("email_length")
    @classmethod
    def _validate_length(cls, value: str) -> str:
        allowed = {"short", "detailed"}
        candidate = value.strip().lower()
        if candidate not in allowed:
            raise ValueError("must be one of: " + ", ".join(sorted(allowed)))
        return candidate


class OutreachResponse(BaseModel):
    """A generated outreach draft."""

    model_config = ConfigDict(from_attributes=True)

    campaign_id: int
    lead_id: int
    email_subject: str
    email_content: str
    campaign_status: str
    tone: str | None = None
    email_length: str | None = None
    communication_goal: str | None = None
    provider: str
    is_mock: bool = Field(
        ..., description="True when the draft came from the labelled offline mock generator"
    )
    notes: str | None = None
    created_at: datetime


class OutreachListResponse(BaseModel):
    """Paginated collection of outreach drafts."""

    total: int
    skip: int
    limit: int
    items: list[OutreachResponse]


class LeadOutreachResponse(BaseModel):
    """Outreach drafts attached to one lead."""

    lead_id: int
    total: int
    items: list[OutreachResponse]


__all__ = [
    "LeadOutreachResponse",
    "OutreachListResponse",
    "OutreachRequest",
    "OutreachResponse",
]
