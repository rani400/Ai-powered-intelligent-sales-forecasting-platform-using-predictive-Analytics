from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.scoring import ScoringRead, ModelStatus
from app.services.lead_service import retrieve
from app.services import scoring_service as svc
from app.ml.evaluate import model_status

router = APIRouter(prefix='/api/scoring', tags=['Module 4 · Lead Scoring'])


@router.get('/model/status', response_model=ModelStatus)
def get_model_status():
    return model_status()


@router.post('/{lead_id}/score', response_model=ScoringRead, status_code=201)
def compute_score(lead_id: int, db: Session = Depends(get_db)):
    return svc.compute(db, retrieve(db, lead_id))


@router.get('/{lead_id}', response_model=ScoringRead)
def latest_score(lead_id: int, db: Session = Depends(get_db)):
    retrieve(db, lead_id)
    record = svc.latest(db, lead_id)
    if not record:
        raise HTTPException(status_code=404, detail='No score saved; run Score first')
    return record
