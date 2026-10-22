"""HTTP client for the SalesGenie AI backend used by the Streamlit interface.

All backend access goes through this module so that error handling is consistent: the UI shows
the backend's actual error message instead of claiming success.
"""

from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT_SECONDS = 30


class ApiError(Exception):
    """Raised when the backend returns an error response."""

    def __init__(self, message: str, status_code: int | None = None, payload: Any = None) -> None:
        self.message = message
        self.status_code = status_code
        self.payload = payload
        super().__init__(message)

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.message


class SalesGenieApi:
    """Thin wrapper around the SalesGenie AI REST API."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.session = requests.Session()

    # -- helpers -----------------------------------------------------------

    def _url(self, path: str) -> str:
        """Build an absolute URL for an API path."""
        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _raise_for_status(response: requests.Response) -> Any:
        """Return the decoded body, raising ApiError with the backend message on failure."""
        if response.status_code >= 400:
            detail = f"Request failed with HTTP {response.status_code}"
            payload: Any = None
            try:
                payload = response.json()
            except ValueError:
                payload = response.text

            if isinstance(payload, dict):
                detail = payload.get("detail") or detail
                errors = payload.get("errors") or []
                if errors:
                    parts = [f"{issue.get('field')}: {issue.get('message')}" for issue in errors]
                    detail = detail + " - " + "; ".join(parts)
            elif isinstance(payload, str) and payload.strip():
                detail = payload.strip()

            raise ApiError(detail, status_code=response.status_code, payload=payload)

        try:
            return response.json()
        except ValueError:
            return response.text

    # -- endpoints ---------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """Return the backend health payload."""
        response = self.session.get(self._url("/health"), timeout=TIMEOUT_SECONDS)
        return self._raise_for_status(response)

    def list_leads(
        self,
        search: str | None = None,
        status: str | None = None,
        industry: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Return a filtered page of lead records."""
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        if industry:
            params["industry"] = industry
        response = self.session.get(self._url("/api/leads"), params=params, timeout=TIMEOUT_SECONDS)
        return self._raise_for_status(response)

    def get_lead(self, lead_id: int) -> dict[str, Any]:
        """Return one lead record."""
        response = self.session.get(self._url(f"/api/leads/{lead_id}"), timeout=TIMEOUT_SECONDS)
        return self._raise_for_status(response)

    def create_lead(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a lead record."""
        response = self.session.post(self._url("/api/leads"), json=payload, timeout=TIMEOUT_SECONDS)
        return self._raise_for_status(response)

    def update_lead(self, lead_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """Apply a partial update to a lead record."""
        response = self.session.put(
            self._url(f"/api/leads/{lead_id}"), json=payload, timeout=TIMEOUT_SECONDS
        )
        return self._raise_for_status(response)

    def delete_lead(self, lead_id: int) -> dict[str, Any]:
        """Delete a lead record."""
        response = self.session.delete(self._url(f"/api/leads/{lead_id}"), timeout=TIMEOUT_SECONDS)
        return self._raise_for_status(response)

    def import_leads(
        self, file_bytes: bytes, filename: str, duplicate_policy: str = "reject"
    ) -> dict[str, Any]:
        """Upload a CSV file for import and return the import report."""
        response = self.session.post(
            self._url("/api/leads/import"),
            files={"file": (filename, file_bytes, "text/csv")},
            data={"duplicate_policy": duplicate_policy, "update_existing": "false"},
            timeout=120,
        )
        return self._raise_for_status(response)

    def get_insights(self, lead_id: int, refresh: bool = False) -> dict[str, Any]:
        """Return the company analysis and qualification score for a lead."""
        response = self.session.get(
            self._url(f"/api/leads/{lead_id}/insights"),
            params={"refresh": str(refresh).lower()},
            timeout=TIMEOUT_SECONDS,
        )
        return self._raise_for_status(response)

    def stats(self) -> dict[str, Any]:
        """Return the operational counters."""
        response = self.session.get(self._url("/api/leads/stats"), timeout=TIMEOUT_SECONDS)
        return self._raise_for_status(response)

    def generate_outreach(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate and store an outreach draft."""
        response = self.session.post(
            self._url("/api/outreach/generate"), json=payload, timeout=TIMEOUT_SECONDS
        )
        return self._raise_for_status(response)

    def list_outreach(self, lead_id: int | None = None) -> dict[str, Any]:
        """Return stored outreach drafts."""
        params: dict[str, Any] = {}
        if lead_id is not None:
            params["lead_id"] = lead_id
        response = self.session.get(
            self._url("/api/outreach"), params=params, timeout=TIMEOUT_SECONDS
        )
        return self._raise_for_status(response)

    def is_reachable(self) -> bool:
        """Return True when the backend answers the health endpoint."""
        try:
            self.health()
        except (requests.RequestException, ApiError):
            return False
        return True
