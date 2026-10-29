from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.intelligence import IntelligenceRead
from app.services.lead_service import retrieve
from app.services import intelligence_service as svc

router = APIRouter(prefix='/api/intelligence', tags=['Module 2 · Lead Intelligence'])


@router.post('/{lead_id}/analyze', response_model=IntelligenceRead, status_code=201)
def analyze(lead_id: int, db: Session = Depends(get_db)):
    return svc.analyze(db, retrieve(db, lead_id))


@router.get('/{lead_id}', response_model=IntelligenceRead)
def latest_analysis(lead_id: int, db: Session = Depends(get_db)):
    retrieve(db, lead_id)
    insight = svc.latest(db, lead_id)
    if not insight:
        raise HTTPException(status_code=404, detail='No analysis saved; run Analyze first')
    return insight
