"""Company analysis API routes.

The intelligence endpoints are always scoped to a single prospect record, so they live under
``/api/leads``. They are separated from the CRUD routes into their own module so that the
analysis surface can evolve independently.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.lead_schema import LeadInsightResponse
from app.services import lead_service
from app.services.lead_intelligence import get_or_generate_insight

router = APIRouter(prefix="/leads", tags=["company-analysis"])


@router.get(
    "/{lead_id}/insights",
    response_model=LeadInsightResponse,
    summary="Retrieve lead intelligence",
)
def read_lead_insights(
    lead_id: int,
    refresh: bool = Query(False, description="Re-run the analysis and store a new result"),
    db: Session = Depends(get_db),
) -> LeadInsightResponse:
    """Return the company analysis and qualification score for a lead."""
    lead = lead_service.get_lead_or_404(db, lead_id)
    return get_or_generate_insight(db, lead, refresh=refresh)
