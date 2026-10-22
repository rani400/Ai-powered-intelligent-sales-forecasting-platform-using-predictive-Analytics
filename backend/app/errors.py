"""Domain exceptions and the single error-to-HTTP translation layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


@dataclass
class FieldIssue:
    """A single field-level problem attached to a domain error."""

    field: str
    message: str


class DomainError(Exception):
    """Base class for expected application errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_detail: str = "Request could not be processed"

    def __init__(
        self,
        detail: str | None = None,
        issues: list[FieldIssue] | None = None,
    ) -> None:
        self.detail = detail or self.default_detail
        self.issues: list[FieldIssue] = issues or []
        super().__init__(self.detail)


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Resource not found"


class DuplicateError(DomainError):
    """Raised when a write would create a duplicate record."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Duplicate record"


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    status_code = 422
    default_detail = "Validation failed"


class UpstreamError(DomainError):
    """Raised when an external provider (for example the LLM) fails."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Upstream provider error"


@dataclass
class ErrorEnvelope:
    """Serialised error body."""

    detail: str
    errors: list[FieldIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-serialisable representation of the envelope."""
        return {
            "detail": self.detail,
            "errors": [{"field": issue.field, "message": issue.message} for issue in self.errors],
        }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the shared error handlers to the application."""

    @app.exception_handler(DomainError)
    async def _handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorEnvelope(exc.detail, exc.issues).to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        issues = [
            FieldIssue(
                field=".".join(str(part) for part in error.get("loc", []) if part != "body")
                or "body",
                message=error.get("msg", "Invalid value"),
            )
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=ErrorEnvelope("Request validation failed", issues).to_dict(),
        )

    @app.exception_handler(ValueError)
    async def _handle_value_error(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorEnvelope(str(exc), [FieldIssue("body", str(exc))]).to_dict(),
        )
