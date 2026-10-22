"""Lead management service layer.

Holds the business rules for creating, listing, updating and deleting prospect records so that
route handlers stay thin (see NFR-7 in the SRS).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import DuplicateError, NotFoundError
from app.models.lead import Lead
from app.schemas.lead_schema import LeadCreate, LeadUpdate
from app.services.duplicate_detection import DuplicateDetector


def get_lead_or_404(db: Session, lead_id: int) -> Lead:
    """Return a lead by id or raise a 404 domain error."""
    lead = db.get(Lead, lead_id)
    if lead is None or not lead.is_active:
        raise NotFoundError(f"Lead {lead_id} not found")
    return lead


def create_lead(db: Session, payload: LeadCreate) -> Lead:
    """Create a lead, rejecting a duplicate email address."""
    detector = DuplicateDetector(db)
    if payload.email:
        match = detector.find_by_email(payload.email)
        if match is not None:
            raise DuplicateError(match.message)

    lead = Lead(
        company_name=payload.company_name,
        industry=payload.industry,
        contact_name=payload.contact_name,
        email=payload.email,
        phone=payload.phone,
        lead_status=payload.lead_status,
        company_size=payload.company_size,
        notes=payload.notes,
        source=payload.source,
        is_active=True,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def list_leads(
    db: Session,
    *,
    search: str | None = None,
    status: str | None = None,
    industry: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[int, list[Lead]]:
    """Return the filtered lead list and the total number of matching rows."""
    filters = [Lead.is_active.is_(True)]

    if search:
        pattern = f"%{search.strip().lower()}%"
        filters.append(
            func.lower(Lead.company_name).like(pattern)
            | func.lower(func.coalesce(Lead.contact_name, "")).like(pattern)
            | func.lower(func.coalesce(Lead.email, "")).like(pattern)
        )
    if status:
        filters.append(Lead.lead_status == status)
    if industry:
        filters.append(Lead.industry == industry)

    total = db.execute(select(func.count()).select_from(Lead).where(*filters)).scalar_one()
    rows = (
        db.execute(
            select(Lead)
            .where(*filters)
            .order_by(Lead.created_at.desc(), Lead.lead_id.desc())
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return total, list(rows)


def update_lead(db: Session, lead: Lead, payload: LeadUpdate) -> Lead:
    """Apply a partial update to a lead."""
    changes = payload.model_dump(exclude_unset=True)

    new_email = changes.get("email")
    if new_email:
        match = DuplicateDetector(db).find_by_email(new_email)
        if match is not None and match.lead_id != lead.lead_id:
            raise DuplicateError(match.message)

    for field, value in changes.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return lead


def delete_lead(db: Session, lead: Lead) -> None:
    """Delete a lead and its dependent insight, score and outreach rows."""
    db.delete(lead)
    db.commit()


def lead_stats(db: Session) -> dict[str, object]:
    """Compute lightweight operational counters for the dashboard."""
    total_leads = db.execute(
        select(func.count()).select_from(Lead).where(Lead.is_active.is_(True))
    ).scalar_one()

    by_status = {
        row[0]: row[1]
        for row in db.execute(
            select(Lead.lead_status, func.count())
            .where(Lead.is_active.is_(True))
            .group_by(Lead.lead_status)
        ).all()
    }
    by_industry = {
        row[0]: row[1]
        for row in db.execute(
            select(Lead.industry, func.count())
            .where(Lead.is_active.is_(True), Lead.industry.is_not(None))
            .group_by(Lead.industry)
        ).all()
    }

    from app.models.lead_score import LeadScore

    scored = db.execute(select(func.count(func.distinct(LeadScore.lead_id)))).scalar_one()
    average_score = db.execute(select(func.avg(LeadScore.score))).scalar()

    return {
        "total_leads": total_leads,
        "active_leads": total_leads,
        "by_status": by_status,
        "by_industry": by_industry,
        "average_score": round(float(average_score), 2) if average_score is not None else None,
        "scored_leads": scored,
    }
