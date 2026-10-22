"""Tests for the lead CRUD API endpoints.

Test case IDs map to the requirement identifiers in ``docs/SRS.md``.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import SECOND_LEAD, VALID_LEAD


def test_tc01_create_valid_lead(client: TestClient) -> None:
    """TC-01 / FR-1.1: a valid lead is created and persisted."""
    response = client.post("/api/leads", json=VALID_LEAD)
    assert response.status_code == 201
    body = response.json()
    assert body["lead_id"] > 0
    assert body["company_name"] == "TechCorp Solutions"
    assert body["lead_status"] == "New"
    assert body["source"] == "manual"
    assert body["is_active"] is True
    assert body["email"] == "sarah@example.com"


def test_tc02_list_leads(client: TestClient) -> None:
    """TC-02 / FR-1.2: leads are listed with a total count."""
    client.post("/api/leads", json=VALID_LEAD)
    client.post("/api/leads", json=SECOND_LEAD)

    response = client.get("/api/leads")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["skip"] == 0 and body["limit"] == 50


def test_tc03_search_and_filter_leads(client: TestClient) -> None:
    """TC-03 / FR-1.2: search and status filters narrow the result set."""
    client.post("/api/leads", json=VALID_LEAD)
    client.post("/api/leads", json={**SECOND_LEAD, "lead_status": "Qualified"})

    assert client.get("/api/leads", params={"search": "techcorp"}).json()["total"] == 1
    assert client.get("/api/leads", params={"search": "mark@example.com"}).json()["total"] == 1
    assert client.get("/api/leads", params={"status": "Qualified"}).json()["total"] == 1
    assert client.get("/api/leads", params={"industry": "Software"}).json()["total"] == 1
    assert client.get("/api/leads", params={"search": "nothing-matches"}).json()["total"] == 0


def test_tc04_retrieve_single_lead(client: TestClient, created_lead: dict) -> None:
    """TC-04 / FR-1.3: a lead is retrievable by its identifier."""
    response = client.get(f"/api/leads/{created_lead['lead_id']}")
    assert response.status_code == 200
    assert response.json()["email"] == "sarah@example.com"


def test_tc05_update_lead(client: TestClient, created_lead: dict) -> None:
    """TC-05 / FR-1.4: a partial update persists and leaves other fields intact."""
    lead_id = created_lead["lead_id"]
    response = client.put(
        f"/api/leads/{lead_id}",
        json={"lead_status": "Qualified", "notes": "Budget confirmed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["lead_status"] == "Qualified"
    assert body["notes"] == "Budget confirmed"
    assert body["company_name"] == "TechCorp Solutions"

    reread = client.get(f"/api/leads/{lead_id}").json()
    assert reread["lead_status"] == "Qualified"


def test_tc06_delete_lead(client: TestClient, created_lead: dict) -> None:
    """TC-06 / FR-1.5: a deleted lead is gone from the API and the list."""
    lead_id = created_lead["lead_id"]
    response = client.delete(f"/api/leads/{lead_id}")
    assert response.status_code == 200
    assert response.json()["lead_id"] == lead_id
    assert client.get(f"/api/leads/{lead_id}").status_code == 404
    assert client.get("/api/leads").json()["total"] == 0


def test_tc07_nonexistent_lead_returns_404(client: TestClient) -> None:
    """TC-07 / FR-1.6: an unknown identifier produces a 404 with a clear message."""
    for method in ("get", "delete"):
        response = getattr(client, method)("/api/leads/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    update = client.put("/api/leads/9999", json={"lead_status": "Qualified"})
    assert update.status_code == 404
    assert "not found" in update.json()["detail"].lower()


def test_tc08_invalid_payload_returns_422(client: TestClient) -> None:
    """TC-08 / FR-1.7 / NFR-1: invalid fields are rejected with field-level detail."""
    response = client.post("/api/leads", json={"email": "sarah@example.com"})
    assert response.status_code == 422
    body = response.json()
    assert body["detail"]
    fields = {issue["field"] for issue in body["errors"]}
    assert "company_name" in fields


def test_tc09_invalid_email_and_status_rejected(client: TestClient) -> None:
    """TC-09 / FR-1.7 / NFR-1: a malformed email or unknown status is rejected."""
    bad_email = client.post("/api/leads", json={**VALID_LEAD, "email": "not-an-email"})
    assert bad_email.status_code == 422
    assert any(issue["field"] == "email" for issue in bad_email.json()["errors"])

    bad_status = client.post("/api/leads", json={**VALID_LEAD, "lead_status": "Archived"})
    assert bad_status.status_code == 422
    assert any(issue["field"] == "lead_status" for issue in bad_status.json()["errors"])


def test_tc10_duplicate_email_returns_409(client: TestClient, created_lead: dict) -> None:
    """FR-1.1 duplicate guard: a second lead with the same email is refused."""
    response = client.post("/api/leads", json={**SECOND_LEAD, "email": "sarah@example.com"})
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_tc11_email_and_whitespace_normalised(client: TestClient) -> None:
    """FR-1.10 / NFR-1: emails are lower-cased and whitespace is trimmed on write."""
    response = client.post(
        "/api/leads",
        json={
            **VALID_LEAD,
            "company_name": "  TechCorp   Solutions  ",
            "email": "  SARAH@Example.COM ",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["company_name"] == "TechCorp Solutions"
    assert body["email"] == "sarah@example.com"


def test_tc12_health_and_stats_endpoints(client: TestClient) -> None:
    """FR-5.1 / API contract: health and counters respond correctly."""
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    client.post("/api/leads", json=VALID_LEAD)
    stats = client.get("/api/leads/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["total_leads"] == 1
    assert body["by_status"] == {"New": 1}
