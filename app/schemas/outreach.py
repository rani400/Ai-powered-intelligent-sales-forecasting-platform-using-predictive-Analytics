from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class OutreachCreate(BaseModel):
    lead_id: int
    tone: Literal['Professional', 'Friendly', 'Concise', 'Persuasive'] = 'Professional'
    communication_goal: Literal['Discovery call', 'Introduction', 'Follow-up', 'Meeting request', 'Re-engagement'] = 'Introduction'
    email_length: Literal['Short', 'Medium', 'Long'] = 'Medium'


class OutreachRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaign_id: int
    lead_id: int
    email_subject: str
    email_content: str
    tone: str
    communication_goal: str
    email_length: str
    provider: str
    is_mock: bool
    campaign_status: str
    created_at: datetime
