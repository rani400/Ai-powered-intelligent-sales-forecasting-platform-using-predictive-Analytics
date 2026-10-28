from sqlalchemy import func, or_, and_, select
from sqlalchemy.orm import Session
from app.models import Lead


def find_duplicate(db: Session, email: str | None, company_name: str, contact_name: str | None, exclude_id: int | None = None):
    clauses = []
    if email:
        clauses.append(func.lower(Lead.email) == email.lower())
    if contact_name:
        clauses.append(and_(func.lower(Lead.company_name) == company_name.lower(),
                            func.lower(Lead.contact_name) == contact_name.lower()))
    if not clauses:
        return None
    stmt = select(Lead).where(or_(*clauses))
    if exclude_id is not None:
        stmt = stmt.where(Lead.lead_id != exclude_id)
    return db.scalars(stmt.order_by(Lead.lead_id)).first()
