"""Request and response schemas for leads, imports, insights and shared responses.

This module groups everything the API accepts and returns for a prospect record: the CRUD
payloads, the CSV import report, the lead intelligence payload and the shared response
envelopes.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.lead import LeadSource, LeadStatus

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^[0-9+()\-.\s]{6,40}$")

_VALID_STATUS_VALUES = {status.value for status in LeadStatus}


def _normalise_text(value: str | None) -> str | None:
    """Trim whitespace and collapse internal runs of spaces."""
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _normalise_email(value: str | None) -> str | None:
    """Lower-case and trim an email address."""
    if value is None:
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def _validate_email_value(value: str | None) -> str | None:
    """Validate an email address without requiring the EmailStr dependency."""
    normalised = _normalise_email(value)
    if normalised is None:
        return None
    if not EMAIL_REGEX.match(normalised):
        raise ValueError("value is not a valid email address")
    return normalised


def _validate_status_value(value: str | None) -> str:
    """Normalise a lead status to its canonical capitalisation."""
    if value is None or not value.strip():
        return LeadStatus.NEW.value
    candidate = value.strip()
    for status in _VALID_STATUS_VALUES:
        if status.lower() == candidate.lower():
            return status
    raise ValueError("must be one of: " + ", ".join(sorted(_VALID_STATUS_VALUES)))


# ---------------------------------------------------------------------------
# Lead CRUD
# ---------------------------------------------------------------------------


class LeadBase(BaseModel):
    """Fields shared by lead create and update schemas."""

    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: Annotated[str, Field(min_length=1, max_length=200)]
    industry: Annotated[str | None, Field(max_length=120)] = None
    contact_name: Annotated[str | None, Field(max_length=120)] = None
    email: Annotated[str | None, Field(max_length=320)] = None
    phone: Annotated[str | None, Field(max_length=40)] = None
    lead_status: Annotated[str, Field(max_length=40)] = LeadStatus.NEW.value
    company_size: Annotated[str | None, Field(max_length=50)] = None
    notes: Annotated[str | None, Field(max_length=2000)] = None

    @field_validator("company_name")
    @classmethod
    def _validate_company_name(cls, value: str) -> str:
        cleaned = _normalise_text(value)
        if not cleaned:
            raise ValueError("company_name is required")
        return cleaned

    @field_validator("industry", "contact_name", "notes", "company_size", mode="before")
    @classmethod
    def _clean_optional_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _normalise_text(value)
        return value

    @field_validator("email", mode="before")
    @classmethod
    def _validate_email(cls, value: Any) -> Any:
        if value is None:
            return None
        return _validate_email_value(str(value))

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, value: Any) -> Any:
        if value is None:
            return None
        candidate = str(value).strip()
        if not candidate:
            return None
        if not PHONE_REGEX.match(candidate):
            raise ValueError("value is not a valid phone number")
        return candidate

    @field_validator("lead_status", mode="before")
    @classmethod
    def _validate_status(cls, value: Any) -> Any:
        if value is None:
            return LeadStatus.NEW.value
        return _validate_status_value(str(value))


class LeadCreate(LeadBase):
    """Payload accepted by ``POST /api/leads``."""

    source: Annotated[str, Field(max_length=40)] = LeadSource.MANUAL.value

    @field_validator("source", mode="before")
    @classmethod
    def _validate_source(cls, value: Any) -> Any:
        if value is None:
            return LeadSource.MANUAL.value
        candidate = str(value).strip().lower()
        allowed = {source.value for source in LeadSource}
        if candidate not in allowed:
            raise ValueError("must be one of: " + ", ".join(sorted(allowed)))
        return candidate


class LeadUpdate(BaseModel):
    """Payload accepted by ``PUT /api/leads/{lead_id}``.

    Every field is optional; only the supplied fields are modified.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    industry: Annotated[str | None, Field(max_length=120)] = None
    contact_name: Annotated[str | None, Field(max_length=120)] = None
    email: Annotated[str | None, Field(max_length=320)] = None
    phone: Annotated[str | None, Field(max_length=40)] = None
    lead_status: Annotated[str | None, Field(max_length=40)] = None
    company_size: Annotated[str | None, Field(max_length=50)] = None
    notes: Annotated[str | None, Field(max_length=2000)] = None
    is_active: bool | None = None

    @field_validator("company_name")
    @classmethod
    def _validate_company_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _normalise_text(value)
        if not cleaned:
            raise ValueError("company_name is required")
        return cleaned

    @field_validator("industry", "contact_name", "notes", "company_size", mode="before")
    @classmethod
    def _clean_optional_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _normalise_text(value)
        return value

    @field_validator("email", mode="before")
    @classmethod
    def _validate_email(cls, value: Any) -> Any:
        if value is None:
            return None
        return _validate_email_value(str(value))

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, value: Any) -> Any:
        if value is None:
            return None
        candidate = str(value).strip()
        if not candidate:
            return None
        if not PHONE_REGEX.match(candidate):
            raise ValueError("value is not a valid phone number")
        return candidate

    @field_validator("lead_status", mode="before")
    @classmethod
    def _validate_status(cls, value: Any) -> Any:
        if value is None:
            return None
        return _validate_status_value(str(value))

    @model_validator(mode="after")
    def _require_at_least_one_field(self) -> LeadUpdate:
        if not self.model_dump(exclude_unset=True):
            raise ValueError("at least one field must be supplied")
        return self


class LeadRead(BaseModel):
    """Lead representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    lead_id: int
    company_name: str
    industry: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    lead_status: str
    company_size: str | None = None
    notes: str | None = None
    source: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------


class LeadImportError(BaseModel):
    """A single rejected or skipped CSV row."""

    row_number: int = Field(..., description="1-based data row number in the CSV file")
    email: str | None = None
    company_name: str | None = None
    reason: str = Field(..., description="Machine-readable rejection reason")
    message: str = Field(..., description="Human-readable explanation")


class LeadImportResponse(BaseModel):
    """Report returned by ``POST /api/leads/import``."""

    total_rows: int = 0
    inserted: int = 0
    updated: int = 0
    duplicates: int = 0
    rejected: int = 0
    inserted_lead_ids: list[int] = Field(default_factory=list)
    errors: list[LeadImportError] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Lead intelligence
# ---------------------------------------------------------------------------


class CompanyProfile(BaseModel):
    """The stored facts about a prospect used to build the analysis."""

    company_name: str
    industry: str | None = None
    contact_name: str | None = None
    email: str | None = None
    lead_status: str
    data_completeness: float = Field(..., ge=0.0, le=1.0)


class ScoreFactor(BaseModel):
    """One weighted contributor to the qualification score."""

    name: str
    weight: float = Field(..., description="Maximum points this factor can contribute")
    raw_value: float = Field(..., description="Normalised factor value between 0 and 1")
    points_awarded: float = Field(..., ge=0.0)
    explanation: str


class QualificationScore(BaseModel):
    """The rule-based qualification score with a full audit trail."""

    score: float = Field(..., ge=0.0, le=100.0)
    band: str = Field(..., description="Qualitative band: Low / Medium / High")
    factors: list[ScoreFactor]
    methodology: str = "rule_based_v1"
    disclaimer: str = (
        "Rule-based prioritisation heuristic computed from stored record fields. "
        "It is not a trained conversion-probability model."
    )


class LeadInsightResponse(BaseModel):
    """Full company intelligence payload for a lead."""

    model_config = ConfigDict(from_attributes=True)

    lead_id: int
    generated_at: datetime
    company_profile: CompanyProfile
    qualification_score: QualificationScore
    business_needs: list[str]
    opportunities: list[str]
    key_insights: list[str]
    information_gaps: list[str]
    is_cached: bool = Field(
        default=False, description="True when the newest stored analysis was returned unchanged"
    )


class InsightRunSummary(BaseModel):
    """Compact summary of a stored insight record."""

    insight_id: int
    lead_id: int
    qualification_score: float | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Shared responses
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """A single field-level validation problem."""

    field: str = Field(..., description="Name of the offending field")
    message: str = Field(..., description="Human readable explanation of the problem")


class ErrorResponse(BaseModel):
    """The consistent error envelope returned by every endpoint."""

    detail: str = Field(..., description="Short summary of what went wrong")
    errors: list[ErrorDetail] = Field(default_factory=list, description="Field-level details")


class MessageResponse(BaseModel):
    """A simple acknowledgement body."""

    detail: str


class DeleteLeadResponse(BaseModel):
    """Response returned after a successful lead deletion."""

    detail: str
    lead_id: int


class LeadListResponse(BaseModel):
    """Paginated collection of leads."""

    total: int = Field(..., description="Total rows matching the filter")
    skip: int
    limit: int
    items: list[LeadRead]


class LeadStatsResponse(BaseModel):
    """Operational counters for the home dashboard."""

    total_leads: int
    active_leads: int
    by_status: dict[str, int]
    by_industry: dict[str, int]
    average_score: float | None = None
    scored_leads: int = 0


class HealthResponse(BaseModel):
    """Service health payload."""

    status: str
    service: str
    version: str


__all__ = [
    "EMAIL_REGEX",
    "PHONE_REGEX",
    "CompanyProfile",
    "DeleteLeadResponse",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "InsightRunSummary",
    "LeadCreate",
    "LeadImportError",
    "LeadImportResponse",
    "LeadInsightResponse",
    "LeadListResponse",
    "LeadRead",
    "LeadStatsResponse",
    "LeadUpdate",
    "MessageResponse",
    "QualificationScore",
    "ScoreFactor",
]
