"""Shared normalisation and validation helpers."""

from __future__ import annotations

import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^[0-9+()\-.\s]{6,40}$")

REQUIRED_CSV_COLUMNS = ("company_name", "email")
OPTIONAL_CSV_COLUMNS = (
    "industry",
    "contact_name",
    "phone",
    "lead_status",
    "company_size",
    "notes",
)


def normalise_text(value: object) -> str | None:
    """Trim and collapse whitespace; return ``None`` for empty results."""
    if value is None:
        return None
    text = str(value).replace("\u00a0", " ").strip()
    if not text:
        return None
    return " ".join(text.split())


def normalise_email(value: object) -> str | None:
    """Lower-case and trim an email address; return ``None`` when empty."""
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def is_valid_email(value: str | None) -> bool:
    """Return True when the value is a syntactically valid email address."""
    if not value:
        return False
    return bool(EMAIL_REGEX.match(value))


def is_valid_phone(value: str | None) -> bool:
    """Return True when the value looks like a usable phone number."""
    if not value:
        return False
    return bool(PHONE_REGEX.match(value.strip()))


def normalise_header(name: object) -> str:
    """Normalise a CSV header cell to its canonical snake_case form."""
    text = str(name or "").strip().lower()
    text = re.sub(r"[\s\-]+", "_", text)
    return re.sub(r"[^a-z0-9_]", "", text)


def build_company_contact_key(company_name: str | None, contact_name: str | None) -> str | None:
    """Build a stable comparison key for a company + contact pair."""
    company = normalise_text(company_name)
    contact = normalise_text(contact_name)
    if not company or not contact:
        return None
    return f"{company.lower()}|{contact.lower()}"
