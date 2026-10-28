from typing import Literal
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.lead import LeadCreate, LeadUpdate, LeadRead, LeadPage, ImportReport, LeadStatus
from app.services import lead_service as svc
from app.config import get_settings

router = APIRouter(prefix='/api/leads', tags=['Module 1 · Lead Management'])


@router.get('', response_model=LeadPage)
def list_leads(search: str | None = None, lead_status: LeadStatus | None = None, industry: str | None = None,
               page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), active_only: bool = False,
               db: Session = Depends(get_db)):
    return svc.list_leads(db, search, lead_status.value if lead_status else None, industry, page, page_size, active_only)


@router.post('', response_model=LeadRead, status_code=201)
def create_lead(body: LeadCreate, db: Session = Depends(get_db)):
    return svc.create(db, body)


@router.post('/import', response_model=ImportReport)
async def import_leads(file: UploadFile = File(...), duplicate_policy: Literal['reject', 'skip', 'update_existing'] = 'reject',
                       db: Session = Depends(get_db)):
    if not (file.filename or '').lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail='Upload a .csv file')
    data = await file.read(get_settings().max_csv_bytes + 1)
    if len(data) > get_settings().max_csv_bytes:
        raise HTTPException(status_code=413, detail='CSV exceeds configured size limit')
    return svc.import_csv(db, data, duplicate_policy)


@router.get('/{lead_id}', response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    return svc.retrieve(db, lead_id)


@router.patch('/{lead_id}', response_model=LeadRead)
def edit_lead(lead_id: int, body: LeadUpdate, db: Session = Depends(get_db)):
    return svc.update(db, lead_id, body)


@router.delete('/{lead_id}', status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    svc.delete(db, lead_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
