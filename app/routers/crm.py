"""Module 5: CRM integration endpoints using the project's existing SQLAlchemy leads."""
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.crm import CRMMappingInfo, CRMPreview, CRMProvider, CRMSyncRequest, CRMSyncResult
from app.services import crm_service, lead_service

router = APIRouter(prefix='/api/crm', tags=['Module 5 · CRM Integration'])


@router.get('/mappings/{provider}', response_model=CRMMappingInfo)
def mappings(provider: CRMProvider):
    """Return mapped CRM fields and explicit exclusions; no network call."""
    return crm_service.get_mapping(provider)


@router.get('/preview/{provider}/{lead_id}', response_model=CRMPreview)
def preview(provider: CRMProvider, lead_id: int, db: Session = Depends(get_db)):
    """Preview provider payload for one saved lead; does not contact the CRM."""
    lead = lead_service.retrieve(db, lead_id)
    return crm_service.build_preview(provider, lead)


@router.post('/sync/{provider}/{lead_id}', response_model=CRMSyncResult)
def sync(provider: CRMProvider, lead_id: int, request: CRMSyncRequest,
         x_crm_admin_key: str | None = Header(default=None),
         db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Default dry-run, or explicit opt-in LIVE sync with an admin key and provider token."""
    lead = lead_service.retrieve(db, lead_id)
    result = crm_service.build_preview(provider, lead)
    if request.dry_run:
        return CRMSyncResult(provider=provider, lead_id=lead_id, status='dry_run',
                             message='Preview only; no CRM request was sent.', preview=result)
    if not request.confirm_live:
        raise HTTPException(status_code=400,
                            detail='Set confirm_live=true explicitly to perform a real CRM write')
    if not settings.crm_live_sync_enabled:
        raise HTTPException(status_code=503, detail='Live CRM sync is disabled in server configuration')
    if not settings.crm_admin_key or not x_crm_admin_key or not secrets.compare_digest(
            x_crm_admin_key, settings.crm_admin_key):
        raise HTTPException(status_code=403, detail='Valid X-CRM-Admin-Key required for live CRM sync')
    if not lead.is_active:
        raise HTTPException(status_code=409, detail='Inactive leads cannot be synced')
    remote_id = crm_service.live_sync(result, settings)
    return CRMSyncResult(provider=provider, lead_id=lead_id, status='synced',
                         remote_id=remote_id,
                         message='CRM confirmed the record write. Salesforce creates; HubSpot upserts.')
