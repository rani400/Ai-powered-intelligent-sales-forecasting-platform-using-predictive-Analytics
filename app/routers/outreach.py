from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.outreach import OutreachCreate, OutreachRead
from app.services.lead_service import retrieve
from app.services import outreach_service as svc

router = APIRouter(prefix='/api/outreach', tags=['Module 3 · AI Outreach'])


@router.post('/generate', response_model=OutreachRead, status_code=201)
def generate(body: OutreachCreate, db: Session = Depends(get_db)):
    return svc.generate(db, retrieve(db, body.lead_id), body)


@router.get('/leads/{lead_id}/drafts', response_model=list[OutreachRead])
def drafts(lead_id: int, limit: int = 20, db: Session = Depends(get_db)):
    retrieve(db, lead_id)
    return svc.history(db, lead_id, max(1, min(limit, 100)))
