"""Input validation and public lead contract."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LeadStatus(str, Enum):
    New = 'New'
    Contacted = 'Contacted'
    Qualified = 'Qualified'
    Converted = 'Converted'


class LeadBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=100)
    contact_name: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    lead_status: LeadStatus = LeadStatus.New
    company_size: str | None = Field(default=None, max_length=30)
    engagement_score: float = Field(default=0, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, max_length=100)
    is_active: bool = True

    @field_validator('company_name', 'industry', 'contact_name', 'phone', 'company_size', 'notes', 'source', mode='before')
    @classmethod
    def clean_text(cls, value):
        if isinstance(value, str):
            return ' '.join(value.strip().split()) or None
        return value

    @field_validator('company_name')
    @classmethod
    def required_company(cls, value):
        if not value:
            raise ValueError('company_name cannot be blank')
        return value

    @field_validator('email', mode='before')
    @classmethod
    def normal_email(cls, value):
        return value.strip().lower() if isinstance(value, str) and value.strip() else None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=100)
    contact_name: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    lead_status: LeadStatus | None = None
    company_size: str | None = Field(default=None, max_length=30)
    engagement_score: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

    @field_validator('company_name', 'industry', 'contact_name', 'phone', 'company_size', 'notes', 'source', mode='before')
    @classmethod
    def clean_text(cls, value):
        if isinstance(value, str):
            return ' '.join(value.strip().split()) or None
        return value

    @field_validator('email', mode='before')
    @classmethod
    def normal_email(cls, value):
        return value.strip().lower() if isinstance(value, str) and value.strip() else None


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    lead_id: int
    created_at: datetime
    updated_at: datetime


class LeadPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[LeadRead]


class ImportIssue(BaseModel):
    row: int
    reason_code: str
    explanation: str


class ImportReport(BaseModel):
    inserted: int = 0
    rejected: int = 0
    duplicate: int = 0
    updated: int = 0
    skipped: int = 0
    issues: list[ImportIssue] = Field(default_factory=list)
