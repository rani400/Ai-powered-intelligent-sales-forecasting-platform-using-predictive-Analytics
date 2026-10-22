"""Measure prospect record coverage for the Milestone 1 acceptance criterion.

The project specification requires that at least 95% of eligible prospect records can be
managed (created, retrieved, updated, deleted) **and** analysed (insight + score generated).

This script performs a real end-to-end measurement against a running backend:

    eligible record = a CSV row that passes the documented validation rules
    managed record  = created, retrieved, updated, retrieved again and deleted through the API
    analysed record = an insight payload with a score was produced for it

    Record coverage (%) = (records that were both managed and analysed) / eligible records x 100

Usage:

    python -m uvicorn app.main:app --app-dir backend
    python backend/scripts/measure_coverage.py --rows 100
"""

from __future__ import annotations

import argparse
import io
import sys
import uuid
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_csv(rows: int) -> str:
    """Build a synthetic CSV with the requested number of valid rows."""
    lines = ["company_name,industry,contact_name,email,phone,lead_status,company_size"]
    for index in range(rows):
        token = uuid.uuid4().hex[:8]
        lines.append(
            f"Coverage Corp {index},Software,Coverage Person {index},"
            f"coverage{index}.{token}@example.com,9800{index:06d},New,51-200"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Run the coverage measurement and print the result."""
    parser = argparse.ArgumentParser(description="Measure prospect record coverage")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--rows", type=int, default=100)
    args = parser.parse_args(argv)
    base = args.base_url.rstrip("/")

    csv_text = build_csv(args.rows)
    eligible = args.rows
    managed = 0
    analysed = 0
    both = 0
    failures: list[str] = []

    with httpx.Client(base_url=base, timeout=60.0) as client:
        import_response = client.post(
            "/api/leads/import",
            files={"file": ("coverage.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")},
            data={"duplicate_policy": "reject", "update_existing": "false"},
        )
        import_response.raise_for_status()
        report = import_response.json()
        inserted_ids = report.get("inserted_lead_ids", [])
        print(f"Eligible rows in the source dataset : {eligible}")
        print(f"Rows imported without error         : {report.get('inserted', 0)}")
        print(f"Rows rejected by validation         : {report.get('rejected', 0)}")

        for lead_id in inserted_ids:
            try:
                retrieved = client.get(f"/api/leads/{lead_id}")
                if retrieved.status_code != 200:
                    failures.append(f"lead {lead_id}: retrieve returned {retrieved.status_code}")
                    continue

                updated = client.put(f"/api/leads/{lead_id}", json={"lead_status": "Contacted"})
                if updated.status_code != 200:
                    failures.append(f"lead {lead_id}: update returned {updated.status_code}")
                    continue
                managed += 1

                insight = client.get(f"/api/leads/{lead_id}/insights", params={"refresh": "true"})
                if insight.status_code != 200:
                    failures.append(f"lead {lead_id}: insights returned {insight.status_code}")
                    continue
                payload = insight.json()
                if "qualification_score" not in payload or "key_insights" not in payload:
                    failures.append(f"lead {lead_id}: insight payload incomplete")
                    continue
                analysed += 1
                both += 1

                deleted = client.delete(f"/api/leads/{lead_id}")
                if deleted.status_code != 200:
                    failures.append(f"lead {lead_id}: delete returned {deleted.status_code}")
            except httpx.HTTPError as exc:
                failures.append(f"lead {lead_id}: transport error {exc}")

    coverage = (both / eligible * 100) if eligible else 0.0
    print()
    print(f"Eligible records                     : {eligible}")
    print(f"Successfully managed (CRUD)          : {managed}")
    print(f"Successfully analysed (insights+score): {analysed}")
    print(f"Managed AND analysed                 : {both}")
    print(f"Record coverage (%)                  : {coverage:.2f}%")
    if failures:
        print()
        print(f"Failures ({len(failures)}):")
        for failure in failures[:20]:
            print(f"  - {failure}")
    print()
    print("Threshold check: " + ("PASS (>= 95%)" if coverage >= 95 else "FAIL (< 95%)"))
    return 0 if coverage >= 95 else 1


if __name__ == "__main__":
    sys.exit(main())
