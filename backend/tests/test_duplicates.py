"""Unit tests for the duplicate detection service."""

from __future__ import annotations

from app.database import get_db
from app.models.lead import Lead
from app.services.duplicate_detection import DuplicateDetector


def _seed(**overrides) -> int:
    """Insert one lead directly and return its id."""
    values = {
        "company_name": "TechCorp Solutions",
        "industry": "Software",
        "contact_name": "Sarah Johnson",
        "email": "sarah@example.com",
        "phone": "9876543210",
        "lead_status": "New",
        "company_size": "51-200",
        "is_active": True,
    }
    values.update(overrides)
    db_gen = get_db()
    db = next(db_gen)
    try:
        lead = Lead(**values)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.lead_id
    finally:
        db_gen.close()


def test_duplicate_by_email_is_detected() -> None:
    """A case-insensitive email match is reported as a duplicate."""
    lead_id = _seed()
    db_gen = get_db()
    db = next(db_gen)
    try:
        detector = DuplicateDetector(db)
        match = detector.find_by_email("  SARAH@Example.com  ")
        assert match is not None
        assert match.reason == "duplicate_email"
        assert match.lead_id == lead_id
    finally:
        db_gen.close()


def test_duplicate_by_company_and_contact_is_detected() -> None:
    """A matching company + contact pair is reported for review."""
    _seed(email=None)
    db_gen = get_db()
    db = next(db_gen)
    try:
        detector = DuplicateDetector(db)
        match = detector.find_by_company_and_contact("techcorp solutions", "SARAH JOHNSON")
        assert match is not None
        assert match.reason == "duplicate_company_contact"
    finally:
        db_gen.close()


def test_detect_prefers_the_email_signal() -> None:
    """The email match wins over the weaker company + contact match."""
    _seed()
    db_gen = get_db()
    db = next(db_gen)
    try:
        detector = DuplicateDetector(db)
        match = detector.detect(
            "sarah@example.com", "TechCorp Solutions", "Sarah Johnson"
        )
        assert match is not None
        assert match.reason == "duplicate_email"
    finally:
        db_gen.close()


def test_no_match_for_a_different_record() -> None:
    """A distinct record is not reported as a duplicate."""
    _seed()
    db_gen = get_db()
    db = next(db_gen)
    try:
        detector = DuplicateDetector(db)
        assert detector.detect("other@example.com", "Other Co", "Jane Doe") is None
    finally:
        db_gen.close()


def test_inactive_leads_are_not_duplicates() -> None:
    """A soft-deleted lead does not block a new record with the same email."""
    _seed(is_active=False)
    db_gen = get_db()
    db = next(db_gen)
    try:
        detector = DuplicateDetector(db)
        assert detector.find_by_email("sarah@example.com") is None
    finally:
        db_gen.close()
