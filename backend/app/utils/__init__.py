"""Utility package for the SalesGenie backend."""

from app.utils.validation import (
    build_company_contact_key,
    is_valid_email,
    is_valid_phone,
    normalise_email,
    normalise_header,
    normalise_text,
)

__all__ = [
    "build_company_contact_key",
    "is_valid_email",
    "is_valid_phone",
    "normalise_email",
    "normalise_header",
    "normalise_text",
]
