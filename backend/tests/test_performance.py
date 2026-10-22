"""Performance checks for the list endpoint and the CSV import path."""

from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient


def test_tc80_list_endpoint_response_time(client: TestClient) -> None:
    """TC-80 / NFR-11: listing 1,000 records responds in well under 500 ms."""
    rows = "\n".join(
        f"Bulk Corp {index},Software,Contact {index},bulk{index}@example.com,90000{index:05d},New"
        for index in range(1000)
    )
    csv_text = "company_name,industry,contact_name,email,phone,lead_status\n" + rows

    import_started = time.perf_counter()
    response = client.post(
        "/api/leads/import",
        files={"file": ("bulk.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")},
        data={"duplicate_policy": "reject", "update_existing": "false"},
    )
    import_elapsed = time.perf_counter() - import_started
    assert response.status_code == 200
    assert response.json()["inserted"] == 1000

    started = time.perf_counter()
    listing = client.get("/api/leads", params={"limit": 200})
    elapsed = time.perf_counter() - started

    assert listing.status_code == 200
    assert listing.json()["total"] == 1000
    assert elapsed < 0.5, f"list endpoint took {elapsed:.3f}s"
    assert import_elapsed < 30.0, f"import took {import_elapsed:.3f}s"


def test_tc81_import_of_one_thousand_rows(client: TestClient) -> None:
    """TC-81 / NFR-12: importing 1,000 rows completes in under 30 seconds."""
    rows = "\n".join(
        f"Company {index},Technology,Person {index},person{index}@example.com,98123{index:05d},New"
        for index in range(1000)
    )
    csv_text = "company_name,industry,contact_name,email,phone,lead_status\n" + rows

    started = time.perf_counter()
    response = client.post(
        "/api/leads/import",
        files={"file": ("bulk.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")},
        data={"duplicate_policy": "reject", "update_existing": "false"},
    )
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert response.json()["inserted"] == 1000
    assert elapsed < 30.0, f"import took {elapsed:.3f}s"
