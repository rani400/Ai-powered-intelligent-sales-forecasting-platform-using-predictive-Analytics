from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional

class LeadCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    industry: str = Field(default="Unknown", max_length=100)
    contact_name: str = Field(default="there", max_length=150)
    contact_title: str = Field(default="", max_length=150)
    email: Optional[str] = None
    phone: Optional[str] = None
    company_size: int = Field(default=0, ge=0)
    annual_revenue: float = Field(default=0, ge=0)
    engagement_score: float = Field(default=0, ge=0, le=100)
    website_visits: int = Field(default=0, ge=0)
    email_opens: int = Field(default=0, ge=0)
    email_clicks: int = Field(default=0, ge=0)
    budget_confirmed: bool = False
    need_identified: bool = False
    decision_maker: bool = False
    lead_status: str = Field(default="New", max_length=50)
    notes: str = ""

class LeadUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_size: Optional[int] = Field(default=None, ge=0)
    annual_revenue: Optional[float] = Field(default=None, ge=0)
    engagement_score: Optional[float] = Field(default=None, ge=0, le=100)
    website_visits: Optional[int] = Field(default=None, ge=0)
    email_opens: Optional[int] = Field(default=None, ge=0)
    email_clicks: Optional[int] = Field(default=None, ge=0)
    budget_confirmed: Optional[bool] = None
    need_identified: Optional[bool] = None
    decision_maker: Optional[bool] = None
    lead_status: Optional[str] = None
    notes: Optional[str] = None

class OutreachRequest(BaseModel):
    tone: str = Field(default="professional", pattern="^(professional|friendly|concise)$")
    goal: str = Field(default="schedule a short discovery call", max_length=200)
