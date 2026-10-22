"""Duplicate detection for prospect records.

The primary duplicate signal is the normalised email address, because the same contact at the
same company is the most common re-entry. A company + contact name pair is used as a secondary,
weaker signal: it is reported for review rather than treated as a hard duplicate, since two
people at one company can legitimately be separate leads.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.utils.validation import build_company_contact_key, normalise_email, normalise_text


@dataclass(frozen=True)
class DuplicateMatch:
    """A record that already exists and matches the candidate being written."""

    reason: str
    lead_id: int
    company_name: str
    message: str


class DuplicateDetector:
    """Detects existing leads that match a candidate record."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_email(self, email: str | None) -> DuplicateMatch | None:
        """Return the active lead that already owns the given email address."""
        normalised = normalise_email(email)
        if not normalised:
            return None

        existing = self.db.execute(
            select(Lead).where(Lead.email == normalised, Lead.is_active.is_(True))
        ).scalar_one_or_none()
        if existing is None:
            return None
        return DuplicateMatch(
            reason="duplicate_email",
            lead_id=existing.lead_id,
            company_name=existing.company_name,
            message=f"A lead with this email already exists (lead_id {existing.lead_id})",
        )

    def find_by_company_and_contact(
        self, company_name: str | None, contact_name: str | None
    ) -> DuplicateMatch | None:
        """Return the lead matching the same company and contact name, if any."""
        key = build_company_contact_key(company_name, contact_name)
        if not key:
            return None

        company = normalise_text(company_name) or ""
        contact = normalise_text(contact_name) or ""

        existing = self.db.execute(
            select(Lead)
            .where(
                func.lower(Lead.company_name) == company.lower(),
                func.lower(Lead.contact_name) == contact.lower(),
                Lead.is_active.is_(True),
            )
            .order_by(Lead.lead_id)
        ).scalars().first()
        if existing is None:
            return None
        return DuplicateMatch(
            reason="duplicate_company_contact",
            lead_id=existing.lead_id,
            company_name=existing.company_name,
            message=(
                "A lead with the same company and contact name already exists "
                f"(lead_id {existing.lead_id})"
            ),
        )

    def detect(
        self,
        email: str | None,
        company_name: str | None = None,
        contact_name: str | None = None,
    ) -> DuplicateMatch | None:
        """Return the strongest duplicate match for a candidate record.

        Email matches win over company + contact matches because they are unambiguous.
        """
        email_match = self.find_by_email(email)
        if email_match is not None:
            return email_match
        return self.find_by_company_and_contact(company_name, contact_name)
