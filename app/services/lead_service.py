"""Lead CRUD and resilient per-row CSV import."""
import csv
import io
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Lead
from app.schemas.lead import LeadCreate, LeadUpdate, ImportReport, ImportIssue
from app.utils.duplicate_detection import find_duplicate
from app.utils.validation import normalize_csv_row


def retrieve(db: Session, lead_id: int) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail='Lead not found')
    return lead


def list_leads(db: Session, search: str | None = None, status: str | None = None, industry: str | None = None,
               page: int = 1, page_size: int = 20, active_only: bool = False):
    query = select(Lead)
    if search:
        pattern = f'%{search.strip().lower()}%'
        query = query.where(or_(func.lower(Lead.company_name).like(pattern),
                                func.lower(Lead.contact_name).like(pattern),
                                func.lower(Lead.email).like(pattern)))
    if status:
        query = query.where(Lead.lead_status == status)
    if industry:
        query = query.where(func.lower(Lead.industry) == industry.strip().lower())
    if active_only:
        query = query.where(Lead.is_active.is_(True))
    count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Lead.created_at.desc(), Lead.lead_id.desc()).offset((page - 1) * page_size).limit(page_size)))
    return {'total': count, 'page': page, 'page_size': page_size, 'items': items}


def create(db: Session, body: LeadCreate):
    data = body.model_dump(mode='json')
    if find_duplicate(db, data.get('email'), data['company_name'], data.get('contact_name')):
        raise HTTPException(status_code=409, detail='Duplicate lead: email or company/contact pair already exists')
    lead = Lead(**data)
    db.add(lead)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='A lead with these unique details already exists')
    db.refresh(lead)
    return lead


def update(db: Session, lead_id: int, body: LeadUpdate):
    lead = retrieve(db, lead_id)
    data = body.model_dump(exclude_unset=True, mode='json')
    for required in ('company_name', 'lead_status', 'engagement_score', 'is_active'):
        if required in data and data[required] is None:
            raise HTTPException(status_code=422, detail=f'{required} must not be null')
    new_company = data.get('company_name', lead.company_name)
    new_contact = data.get('contact_name', lead.contact_name)
    new_email = data.get('email', lead.email)
    if find_duplicate(db, new_email, new_company, new_contact, exclude_id=lead_id):
        raise HTTPException(status_code=409, detail='Duplicate lead: email or company/contact pair already exists')
    for key, value in data.items():
        setattr(lead, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Unique field conflict')
    db.refresh(lead)
    return lead


def delete(db: Session, lead_id: int):
    lead = retrieve(db, lead_id)
    db.delete(lead)
    db.commit()


def import_csv(db: Session, content: bytes, duplicate_policy: str) -> ImportReport:
    report = ImportReport()
    try:
        decoded = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail='CSV must have a header row')
        normalized_headers = {h.strip().lower().replace(' ', '_') for h in reader.fieldnames if h}
        if 'company_name' not in normalized_headers:
            raise HTTPException(status_code=400, detail='Missing required CSV header: company_name')
        for row_number, raw in enumerate(reader, start=2):
            if all(not str(value or '').strip() for value in raw.values()):
                report.skipped += 1
                continue
            try:
                row = normalize_csv_row(raw)
                body = LeadCreate.model_validate(row)
            except ValidationError as exc:
                report.rejected += 1
                first = exc.errors()[0]
                field = '.'.join(map(str, first['loc']))
                report.issues.append(ImportIssue(row=row_number, reason_code='INVALID_DATA',
                                                 explanation=f'{field}: {first["msg"]}'))
                continue
            data = body.model_dump(mode='json')
            duplicate = find_duplicate(db, data.get('email'), data['company_name'], data.get('contact_name'))
            if duplicate:
                report.duplicate += 1
                if duplicate_policy == 'update_existing':
                    # Only overwrite CSV fields that were provided; preserve existing otherwise.
                    for key in row:
                        if row[key] is not None:
                            setattr(duplicate, key, data[key])
                    try:
                        db.commit()
                        report.updated += 1
                    except IntegrityError:
                        db.rollback()
                        report.rejected += 1
                        report.issues.append(ImportIssue(row=row_number, reason_code='UNIQUE_CONFLICT',
                                                         explanation='Updated row would violate a unique constraint'))
                elif duplicate_policy == 'skip':
                    report.skipped += 1
                else:
                    report.rejected += 1
                    report.issues.append(ImportIssue(row=row_number, reason_code='DUPLICATE_LEAD',
                                                     explanation='Matching email or company/contact already exists'))
                continue
            db.add(Lead(**data))
            try:
                db.commit()
                report.inserted += 1
            except IntegrityError:
                db.rollback()
                report.rejected += 1
                report.issues.append(ImportIssue(row=row_number, reason_code='UNIQUE_CONFLICT',
                                                 explanation='Row violates a database uniqueness constraint'))
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail='CSV must be encoded as UTF-8')
    except csv.Error as exc:
        raise HTTPException(status_code=400, detail=f'Malformed CSV: {exc}')
    return report
