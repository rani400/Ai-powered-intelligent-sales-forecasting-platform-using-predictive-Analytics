"""AI outreach generation API routes.

Covers both the campaign collection (``/api/outreach``) and the per-lead draft collection
(``/api/leads/{lead_id}/outreach``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.outreach_campaign import CampaignStatus, OutreachCampaign
from app.schemas.outreach_schema import (
    LeadOutreachResponse,
    OutreachListResponse,
    OutreachRequest,
    OutreachResponse,
)
from app.services import lead_service
from app.services.outreach_generator import OutreachGenerator

router = APIRouter(tags=["outreach"])


@router.post(
    "/outreach/generate",
    response_model=OutreachResponse,
    summary="Generate an outreach draft",
)
def generate_outreach(
    payload: OutreachRequest,
    db: Session = Depends(get_db),
) -> OutreachResponse:
    """Generate a personalised email draft for a lead and store it as a draft."""
    lead = lead_service.get_lead_or_404(db, payload.lead_id)

    company_name = payload.company_name or lead.company_name
    contact_name = payload.contact_name if payload.contact_name is not None else lead.contact_name
    industry = payload.industry if payload.industry is not None else lead.industry

    generator = OutreachGenerator()
    draft = generator.generate(
        company_name=company_name,
        contact_name=contact_name,
        industry=industry,
        product_or_service=payload.product_or_service,
        tone=payload.tone,
        email_length=payload.email_length,
        communication_goal=payload.communication_goal,
    )

    campaign = OutreachCampaign(
        lead_id=lead.lead_id,
        email_subject=draft.subject,
        email_content=draft.body,
        campaign_status=CampaignStatus.DRAFT,
        tone=payload.tone,
        email_length=payload.email_length,
        communication_goal=payload.communication_goal,
        provider=draft.provider,
        is_mock=draft.is_mock,
        generation_latency_ms=draft.latency_ms,
        notes=draft.notes,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return OutreachResponse.model_validate(campaign)


@router.get(
    "/outreach",
    response_model=OutreachListResponse,
    summary="List outreach drafts",
)
def list_outreach(
    lead_id: int | None = Query(None, gt=0, description="Filter by lead"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> OutreachListResponse:
    """Return stored outreach drafts, newest first."""
    query = db.query(OutreachCampaign)
    if lead_id is not None:
        query = query.filter(OutreachCampaign.lead_id == lead_id)
    total = query.count()
    rows = (
        query.order_by(OutreachCampaign.created_at.desc(), OutreachCampaign.campaign_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return OutreachListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[OutreachResponse.model_validate(row) for row in rows],
    )


@router.get(
    "/leads/{lead_id}/outreach",
    response_model=LeadOutreachResponse,
    summary="Retrieve outreach drafts for a lead",
)
def read_lead_outreach(
    lead_id: int,
    db: Session = Depends(get_db),
) -> LeadOutreachResponse:
    """Return every outreach draft stored against a lead."""
    lead = lead_service.get_lead_or_404(db, lead_id)
    rows = (
        db.query(OutreachCampaign)
        .filter(OutreachCampaign.lead_id == lead.lead_id)
        .order_by(OutreachCampaign.created_at.desc(), OutreachCampaign.campaign_id.desc())
        .all()
    )
    return LeadOutreachResponse(
        lead_id=lead.lead_id,
        total=len(rows),
        items=[OutreachResponse.model_validate(row) for row in rows],
    )
