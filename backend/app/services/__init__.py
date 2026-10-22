"""Service layer package for the SalesGenie backend."""

from app.services.duplicate_detection import DuplicateDetector, DuplicateMatch
from app.services.lead_import import (
    CSVImportError,
    DuplicatePolicy,
    ImportErrorKind,
    ImportResult,
    LeadImportService,
)
from app.services.lead_intelligence import (
    calculate_qualification_score,
    generate_insight,
    get_or_generate_insight,
    persist_insight,
)
from app.services.outreach_generator import GeneratedDraft, OutreachGenerator

__all__ = [
    "CSVImportError",
    "DuplicateDetector",
    "DuplicateMatch",
    "DuplicatePolicy",
    "GeneratedDraft",
    "ImportErrorKind",
    "ImportResult",
    "LeadImportService",
    "OutreachGenerator",
    "calculate_qualification_score",
    "generate_insight",
    "get_or_generate_insight",
    "persist_insight",
]
