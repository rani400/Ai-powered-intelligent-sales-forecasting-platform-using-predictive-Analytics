"""Module 5: provider field mapping, preview, guarded sync and audit log."""
import secrets
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.config import Settings, get_settings
from app.database import get_db
from app.models.crm_sync_log import CRMSyncLog
from app.schemas.crm import CRMMappingInfo, CRMPreview, CRMProvider, CRMSyncRequest, CRMSyncResult
from app.services import crm_service, lead_service

router = APIRouter(prefix='/api/crm', tags=['Module 5 · CRM Integration'])


def _require_admin(settings: Settings, key: str | None):
    if not settings.crm_admin_key or not key or not secrets.compare_digest(key, settings.crm_admin_key):
        raise HTTPException(403, 'Valid X-CRM-Admin-Key required')


def _record(db: Session, preview: CRMPreview, status: str, message: str, remote_id: str | None = None):
    db.add(CRMSyncLog(lead_id=preview.lead_id, provider=preview.provider.value,
                      operation=preview.operation, status=status,
                      message=message, remote_id=remote_id))
    db.commit()


@router.get('/mappings/{provider}', response_model=CRMMappingInfo)
def mappings(provider: CRMProvider):
    return crm_service.get_mapping(provider)


@router.get('/preview/{provider}/{lead_id}', response_model=CRMPreview)
def preview(provider: CRMProvider, lead_id: int, db: Session = Depends(get_db)):
    lead = lead_service.retrieve(db, lead_id)
    return crm_service.build_preview(provider, lead)


@router.post('/sync/{provider}/{lead_id}', response_model=CRMSyncResult)
def sync(provider: CRMProvider, lead_id: int, request: CRMSyncRequest,
         x_crm_admin_key: str | None = Header(default=None),
         db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    lead = lead_service.retrieve(db, lead_id)
    result = crm_service.build_preview(provider, lead)
    if request.dry_run:
        _record(db, result, 'dry_run', 'No CRM request was sent')
        return CRMSyncResult(provider=provider, lead_id=lead_id, status='dry_run',
                             message='Preview only; no CRM request was sent.', preview=result)
    if not request.confirm_live:
        raise HTTPException(400, 'Set confirm_live=true explicitly to perform a real CRM write')
    if not settings.crm_live_sync_enabled:
        raise HTTPException(503, 'Live CRM sync is disabled in server configuration')
    _require_admin(settings, x_crm_admin_key)
    if not lead.is_active:
        raise HTTPException(409, 'Inactive leads cannot be synced')
    try:
        remote_id = crm_service.live_sync(result, settings)
    except HTTPException:
        _record(db, result, 'failed', 'Provider sync failed; details withheld')
        raise
    _record(db, result, 'synced', 'Provider confirmed the record write', remote_id)
    return CRMSyncResult(provider=provider, lead_id=lead_id, status='synced',
                         remote_id=remote_id,
                         message='CRM confirmed the record write. Salesforce creates; HubSpot upserts.')


@router.get('/logs/{lead_id}')
def logs(lead_id: int, x_crm_admin_key: str | None = Header(default=None),
         db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    _require_admin(settings, x_crm_admin_key)
    lead_service.retrieve(db, lead_id)
    records = db.scalars(select(CRMSyncLog).where(CRMSyncLog.lead_id == lead_id)
                         .order_by(CRMSyncLog.created_at.desc(), CRMSyncLog.log_id.desc())
                         .limit(100)).all()
    return [{'log_id': x.log_id, 'provider': x.provider, 'lead_id': x.lead_id,
             'status': x.status, 'operation': x.operation, 'remote_id': x.remote_id,
             'message': x.message, 'created_at': x.created_at.isoformat()} for x in records]
