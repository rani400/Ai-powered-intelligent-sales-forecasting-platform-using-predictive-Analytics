"""Lead management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import DomainError
from app.schemas.lead_schema import (
    DeleteLeadResponse,
    LeadCreate,
    LeadImportResponse,
    LeadListResponse,
    LeadRead,
    LeadStatsResponse,
    LeadUpdate,
)
from app.services import lead_service
from app.services.lead_import import CSVImportError, DuplicatePolicy, LeadImportService

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/stats", response_model=LeadStatsResponse, summary="Operational lead counters")
def read_lead_stats(db: Session = Depends(get_db)) -> LeadStatsResponse:
    """Return counters for the dashboard home page."""
    return LeadStatsResponse(**lead_service.lead_stats(db))


@router.post(
    "",
    response_model=LeadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a lead",
)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> LeadRead:
    """Create a validated prospect record."""
    return LeadRead.model_validate(lead_service.create_lead(db, payload))


@router.post(
    "/import",
    response_model=LeadImportResponse,
    summary="Import leads from a CSV file",
)
async def import_leads(
    file: UploadFile = File(..., description="CSV file with at least company_name and email"),
    duplicate_policy: str = Form("reject", description="'reject' or 'skip'"),
    update_existing: bool = Form(False),
    db: Session = Depends(get_db),
) -> LeadImportResponse:
    """Import prospect records from an uploaded CSV file."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise DomainError("Uploaded file must be a .csv file")

    raw = await file.read()
    if not raw.strip():
        raise DomainError("The uploaded file is empty")

    policy = DuplicatePolicy.SKIP if duplicate_policy == "skip" else DuplicatePolicy.REJECT
    service = LeadImportService(db, duplicate_policy=policy, update_existing=update_existing)

    try:
        result = service.import_csv(raw)
    except CSVImportError as exc:
        raise DomainError(str(exc)) from exc

    return LeadImportResponse(**result.to_dict())


@router.get("", response_model=LeadListResponse, summary="Retrieve leads")
def list_leads(
    search: str | None = Query(None, description="Match company, contact or email"),
    status_filter: str | None = Query(None, alias="status", description="Filter by lead status"),
    industry: str | None = Query(None, description="Filter by industry"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> LeadListResponse:
    """Return a filtered, paginated list of prospect records."""
    total, rows = lead_service.list_leads(
        db,
        search=search,
        status=status_filter,
        industry=industry,
        skip=skip,
        limit=limit,
    )
    return LeadListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[LeadRead.model_validate(row) for row in rows],
    )


@router.get(
    "/{lead_id}",
    response_model=LeadRead,
    summary="Retrieve one lead",
)
def read_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadRead:
    """Return a single prospect record."""
    return LeadRead.model_validate(lead_service.get_lead_or_404(db, lead_id))


@router.put(
    "/{lead_id}",
    response_model=LeadRead,
    summary="Update a lead",
)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)) -> LeadRead:
    """Apply a partial update to a prospect record."""
    lead = lead_service.get_lead_or_404(db, lead_id)
    return LeadRead.model_validate(lead_service.update_lead(db, lead, payload))


@router.delete(
    "/{lead_id}",
    response_model=DeleteLeadResponse,
    summary="Delete a lead",
)
def delete_lead(lead_id: int, db: Session = Depends(get_db)) -> DeleteLeadResponse:
    """Delete a prospect record and its dependent rows."""
    lead = lead_service.get_lead_or_404(db, lead_id)
    lead_service.delete_lead(db, lead)
    return DeleteLeadResponse(detail=f"Lead {lead_id} deleted", lead_id=lead_id)
