"""End-to-end demo walkthrough against a running backend.

Exercises the full Milestone 1 workflow over HTTP and prints a readable report. This is the
script used to capture demonstration evidence.

Usage (backend must be running):

    python -m uvicorn app.main:app --app-dir backend
    python backend/scripts/demo_walkthrough.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CSV = PROJECT_ROOT / "data" / "sample_leads.csv"


def _section(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def _show(label: str, payload: object) -> None:
    """Print a labelled JSON payload."""
    print(f"\n--- {label} ---")
    print(json.dumps(payload, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    """Run the walkthrough."""
    parser = argparse.ArgumentParser(description="SalesGenie AI demo walkthrough")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args(argv)
    base = args.base_url.rstrip("/")

    with httpx.Client(base_url=base, timeout=30.0) as client:
        _section("1. Health check")
        health = client.get("/health")
        _show("GET /health", health.json())

        _section("2. CSV import of data/sample_leads.csv")
        with SAMPLE_CSV.open("rb") as handle:
            import_response = client.post(
                "/api/leads/import",
                files={"file": (SAMPLE_CSV.name, handle, "text/csv")},
                data={"duplicate_policy": "reject", "update_existing": "false"},
            )
        _show("POST /api/leads/import", import_response.json())

        _section("3. Lead list")
        listing = client.get("/api/leads", params={"limit": 10})
        _show("GET /api/leads", listing.json())

        lead_id = listing.json()["items"][0]["lead_id"]

        _section("4. Lead intelligence and qualification score")
        insights = client.get(f"/api/leads/{lead_id}/insights", params={"refresh": "true"})
        _show(f"GET /api/leads/{lead_id}/insights", insights.json())

        _section("5. Outreach draft generation")
        outreach = client.post(
            "/api/outreach/generate",
            json={
                "lead_id": lead_id,
                "product_or_service": "SalesGenie AI lead intelligence platform",
                "communication_goal": "meeting",
                "tone": "professional",
                "email_length": "short",
            },
        )
        _show("POST /api/outreach/generate", outreach.json())

        _section("6. Stored drafts for the lead")
        drafts = client.get(f"/api/leads/{lead_id}/outreach")
        _show(f"GET /api/leads/{lead_id}/outreach", drafts.json())

        _section("7. Dashboard counters")
        _show("GET /api/leads/stats", client.get("/api/leads/stats").json())

        _section("8. Validation evidence - invalid payload")
        invalid = client.post("/api/leads", json={"email": "not-an-email"})
        _show(f"POST /api/leads (invalid) -> HTTP {invalid.status_code}", invalid.json())

        _section("9. Duplicate evidence - same email again")
        duplicate = client.post(
            "/api/leads",
            json={
                "company_name": "TechCorp Solutions",
                "email": listing.json()["items"][0]["email"],
            },
        )
        _show(f"POST /api/leads (duplicate) -> HTTP {duplicate.status_code}", duplicate.json())

    print()
    print("Walkthrough complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
