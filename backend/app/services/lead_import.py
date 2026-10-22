"""CSV lead import service.

The service parses an uploaded CSV, validates every row independently, detects duplicates and
reports exactly what happened to each row. A malformed row never prevents valid rows from being
stored, and a valid row is never written half-way.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadSource, LeadStatus
from app.services.duplicate_detection import DuplicateDetector
from app.utils.validation import (
    REQUIRED_CSV_COLUMNS,
    is_valid_email,
    normalise_email,
    normalise_header,
    normalise_text,
)

_VALID_STATUSES = {status.value.lower(): status.value for status in LeadStatus}


class DuplicatePolicy(str, Enum):
    """How the importer reacts to a duplicate record."""

    REJECT = "reject"
    SKIP = "skip"


class ImportErrorKind(str, Enum):
    """Machine-readable rejection reasons."""

    MISSING_COMPANY_NAME = "missing_company_name"
    MISSING_EMAIL = "missing_email"
    INVALID_EMAIL = "invalid_email"
    INVALID_STATUS = "invalid_status"
    DUPLICATE_EMAIL = "duplicate_email"
    DUPLICATE_COMPANY_CONTACT = "duplicate_company_contact"
    INVALID_ROW = "invalid_row"


@dataclass
class RowError:
    """A single rejected or skipped row."""

    row_number: int
    email: str | None
    company_name: str | None
    reason: str
    message: str

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-serialisable representation of the row error."""
        return {
            "row_number": self.row_number,
            "email": self.email,
            "company_name": self.company_name,
            "reason": self.reason,
            "message": self.message,
        }


@dataclass
class ImportResult:
    """Aggregated outcome of a CSV import."""

    total_rows: int = 0
    inserted: int = 0
    updated: int = 0
    duplicates: int = 0
    rejected: int = 0
    inserted_lead_ids: list[int] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-serialisable import report."""
        return {
            "total_rows": self.total_rows,
            "inserted": self.inserted,
            "updated": self.updated,
            "duplicates": self.duplicates,
            "rejected": self.rejected,
            "inserted_lead_ids": list(self.inserted_lead_ids),
            "errors": [error.to_dict() for error in self.errors],
        }


class CSVImportError(Exception):
    """Raised when the uploaded file cannot be processed at all."""


class LeadImportService:
    """Validates and imports prospect records from CSV content."""

    def __init__(
        self,
        db: Session,
        duplicate_policy: DuplicatePolicy = DuplicatePolicy.REJECT,
        update_existing: bool = False,
    ) -> None:
        self.db = db
        self.duplicate_policy = duplicate_policy
        self.update_existing = update_existing

    # -- parsing -----------------------------------------------------------

    @staticmethod
    def parse_csv(raw: bytes | str) -> list[dict[str, str]]:
        """Parse raw CSV content into a list of normalised row dictionaries.

        Raises:
            CSVImportError: when the payload is empty or is not parseable CSV.
        """
        if isinstance(raw, bytes):
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError as exc:  # pragma: no cover - defensive
                raise CSVImportError("File must be a UTF-8 encoded CSV") from exc
        else:
            text = raw

        if not text.strip():
            raise CSVImportError("The uploaded file is empty")

        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise CSVImportError("The uploaded file has no header row")

        headers = {normalise_header(name) for name in reader.fieldnames if name is not None}
        missing = [column for column in REQUIRED_CSV_COLUMNS if column not in headers]
        if missing:
            raise CSVImportError("Missing required column(s): " + ", ".join(missing))

        rows: list[dict[str, str]] = []
        for raw_row in reader:
            row = {
                normalise_header(key): ("" if value is None else str(value))
                for key, value in raw_row.items()
                if key is not None
            }
            row["__row_number__"] = str(len(rows) + 2)  # +1 for header, +1 for 1-based
            rows.append(row)
        return rows

    # -- validation --------------------------------------------------------

    @staticmethod
    def _validate_row(row: dict[str, str]) -> tuple[dict[str, str | None] | None, RowError | None]:
        """Validate and normalise one CSV row.

        Returns:
            A tuple of ``(normalised_values, error)``. Exactly one element is not ``None``.
        """
        row_number = int(row.get("__row_number__", 0))
        company_name = normalise_text(row.get("company_name"))
        email = normalise_email(row.get("email"))
        contact_name = normalise_text(row.get("contact_name"))
        industry = normalise_text(row.get("industry"))
        phone = normalise_text(row.get("phone"))
        company_size = normalise_text(row.get("company_size"))
        notes = normalise_text(row.get("notes"))

        raw_status = normalise_text(row.get("lead_status"))
        lead_status = LeadStatus.NEW.value
        if raw_status:
            resolved = _VALID_STATUSES.get(raw_status.lower())
            if resolved is None:
                return None, RowError(
                    row_number=row_number,
                    email=email,
                    company_name=company_name,
                    reason=ImportErrorKind.INVALID_STATUS.value,
                    message=(
                        f"Unknown lead_status '{raw_status}'. Allowed values: "
                        + ", ".join(sorted(_VALID_STATUSES.values()))
                    ),
                )
            lead_status = resolved

        if not company_name:
            return None, RowError(
                row_number=row_number,
                email=email,
                company_name=None,
                reason=ImportErrorKind.MISSING_COMPANY_NAME.value,
                message="company_name is required",
            )

        if not email:
            return None, RowError(
                row_number=row_number,
                email=None,
                company_name=company_name,
                reason=ImportErrorKind.MISSING_EMAIL.value,
                message="email is required",
            )

        if not is_valid_email(email):
            return None, RowError(
                row_number=row_number,
                email=email,
                company_name=company_name,
                reason=ImportErrorKind.INVALID_EMAIL.value,
                message="value is not a valid email address",
            )

        return {
            "company_name": company_name,
            "email": email,
            "contact_name": contact_name,
            "industry": industry,
            "phone": phone,
            "company_size": company_size,
            "lead_status": lead_status,
            "notes": notes,
        }, None

    # -- import ------------------------------------------------------------

    def import_rows(self, rows: list[dict[str, str]]) -> ImportResult:
        """Validate and store every parsed row, returning the aggregated report."""
        result = ImportResult(total_rows=len(rows))
        detector = DuplicateDetector(self.db)

        for row in rows:
            values, error = self._validate_row(row)
            if error is not None:
                result.rejected += 1
                result.errors.append(error)
                continue

            assert values is not None  # narrowed by the contract above
            duplicate = detector.detect(
                email=values["email"],
                company_name=values["company_name"],
                contact_name=values["contact_name"],
            )

            if duplicate is not None:
                if self.update_existing:
                    existing = self.db.get(Lead, duplicate.lead_id)
                    if existing is not None:
                        existing.company_name = values["company_name"] or existing.company_name
                        existing.industry = values["industry"] or existing.industry
                        existing.contact_name = values["contact_name"] or existing.contact_name
                        existing.email = values["email"] or existing.email
                        existing.phone = values["phone"] or existing.phone
                        existing.lead_status = values["lead_status"] or existing.lead_status
                        existing.company_size = values["company_size"] or existing.company_size
                        existing.notes = values["notes"] or existing.notes
                        result.updated += 1
                        continue
                if self.duplicate_policy == DuplicatePolicy.SKIP:
                    result.duplicates += 1
                    result.errors.append(
                        RowError(
                            row_number=int(row.get("__row_number__", 0)),
                            email=values["email"],
                            company_name=values["company_name"],
                            reason=duplicate.reason,
                            message=f"{duplicate.message} - row skipped",
                        )
                    )
                else:
                    result.duplicates += 1
                    result.rejected += 1
                    result.errors.append(
                        RowError(
                            row_number=int(row.get("__row_number__", 0)),
                            email=values["email"],
                            company_name=values["company_name"],
                            reason=duplicate.reason,
                            message=duplicate.message,
                        )
                    )
                continue

            lead = Lead(
                company_name=values["company_name"],
                industry=values["industry"],
                contact_name=values["contact_name"],
                email=values["email"],
                phone=values["phone"],
                company_size=values["company_size"],
                lead_status=values["lead_status"] or LeadStatus.NEW.value,
                notes=values["notes"],
                source=LeadSource.CSV_IMPORT.value,
                is_active=True,
            )
            self.db.add(lead)
            self.db.flush()
            result.inserted += 1
            result.inserted_lead_ids.append(lead.lead_id)

        self.db.commit()
        return result

    def import_csv(self, raw: bytes | str) -> ImportResult:
        """Parse and import raw CSV content in one step."""
        rows = self.parse_csv(raw)
        return self.import_rows(rows)
