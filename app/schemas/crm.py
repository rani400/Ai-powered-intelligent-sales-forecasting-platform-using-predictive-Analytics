"""Validated CRM integration request / response contracts."""
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class CRMProvider(str, Enum):
    salesforce = 'salesforce'
    hubspot = 'hubspot'


class CRMFieldMapping(BaseModel):
    source: str
    destination: str


class CRMMappingInfo(BaseModel):
    provider: CRMProvider
    target_object: str
    fields: list[CRMFieldMapping]
    not_synced: list[str]


class CRMPreview(BaseModel):
    provider: CRMProvider
    lead_id: int
    target_object: str
    operation: str
    payload: dict[str, Any]


class CRMSyncRequest(BaseModel):
    dry_run: bool = True
    confirm_live: bool = False


class CRMSyncResult(BaseModel):
    provider: CRMProvider
    lead_id: int
    status: Literal['dry_run', 'synced']
    remote_id: str | None = None
    message: str
    preview: CRMPreview | None = None


class CRMSyncLogRead(BaseModel):
    model_config = {'from_attributes': True}
    log_id: int
    provider: str
    lead_id: int
    operation: str
    status: str
    remote_id: str | None
    message: str | None
    created_at: str | None = None
