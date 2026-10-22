"""Tests for CSV import, validation and duplicate detection."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from tests.conftest import VALID_LEAD

VALID_CSV = """company_name,industry,contact_name,email,phone,lead_status
TechCorp Solutions,Software,Sarah Johnson,sarah@example.com,9876543210,New
Innovate Labs,Technology,Mark Chen,mark@example.com,9876543211,New
DataFlow Systems,Analytics,Emily Davis,emily@example.com,9876543212,Qualified
"""

MIXED_CSV = """company_name,industry,contact_name,email,phone,lead_status
Acme Analytics,Analytics,Dana Fox,dana@acme.example.com,9000000001,New
Broken Email Co,Software,No Reply,not-an-email,9000000002,New
,Technology,Nameless Contact,nameless@example.com,9000000003,New
Unknown Status Ltd,Software,Pat Patel,pat@example.com,9000000004,Archived
"""


def _upload(client: TestClient, content: str, filename: str = "leads.csv", **form: str):
    """Post a CSV file to the import endpoint."""
    data = {"duplicate_policy": "reject", "update_existing": "false"}
    data.update(form)
    return client.post(
        "/api/leads/import",
        files={"file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv")},
        data=data,
    )


def test_tc20_import_valid_csv(client: TestClient) -> None:
    """TC-20 / FR-1.8: a valid CSV file imports every row."""
    response = _upload(client, VALID_CSV)
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 3
    assert body["inserted"] == 3
    assert body["rejected"] == 0
    assert body["duplicates"] == 0
    assert len(body["inserted_lead_ids"]) == 3
    assert client.get("/api/leads").json()["total"] == 3


def test_tc21_missing_required_columns_rejected(client: TestClient) -> None:
    """TC-21 / FR-1.9: a file without the required columns is refused."""
    response = _upload(client, "name,sector\nAcme,Software\n")
    assert response.status_code == 400
    assert "missing required column" in response.json()["detail"].lower()


def test_tc22_empty_file_rejected(client: TestClient) -> None:
    """TC-22 / FR-1.9: an empty file is refused with a clear message."""
    response = _upload(client, "")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_tc23_invalid_email_row_rejected_others_kept(client: TestClient) -> None:
    """TC-23 / FR-1.9 / NFR-3: one bad row does not block the valid rows."""
    response = _upload(client, MIXED_CSV)
    assert response.status_code == 200
    body = response.json()
    assert body["inserted"] == 1
    assert body["rejected"] == 3
    reasons = {error["reason"] for error in body["errors"]}
    assert "invalid_email" in reasons
    assert "missing_company_name" in reasons
    assert "invalid_status" in reasons
    assert client.get("/api/leads").json()["total"] == 1


def test_tc24_partially_invalid_file_reports_each_row(client: TestClient) -> None:
    """TC-24 / FR-1.12: every rejected row is reported with its row number."""
    response = _upload(client, MIXED_CSV)
    body = response.json()
    row_numbers = {error["row_number"] for error in body["errors"]}
    assert row_numbers == {3, 4, 5}
    for error in body["errors"]:
        assert error["message"]
        assert error["reason"]


def test_tc25_import_normalises_values(client: TestClient) -> None:
    """TC-25 / FR-1.10: CSV values are normalised on the way in."""
    csv_text = "company_name,email\n  TechCorp   Solutions  ,  SARAH@Example.COM \n"
    response = _upload(client, csv_text)
    assert response.status_code == 200
    assert response.json()["inserted"] == 1

    lead = client.get("/api/leads").json()["items"][0]
    assert lead["company_name"] == "TechCorp Solutions"
    assert lead["email"] == "sarah@example.com"


def test_tc26_duplicate_email_detected_on_import(client: TestClient) -> None:
    """TC-26 / FR-1.11: a duplicate email in the file is detected and rejected."""
    client.post("/api/leads", json=VALID_LEAD)

    csv_text = (
        "company_name,email\n"
        "TechCorp Solutions,sarah@example.com\n"
        "Another Company,sarah@example.com\n"
    )
    response = _upload(client, csv_text)
    body = response.json()
    assert body["inserted"] == 0
    assert body["duplicates"] == 2
    assert all(error["reason"] == "duplicate_email" for error in body["errors"])
    assert client.get("/api/leads").json()["total"] == 1


def test_tc27_duplicate_policy_skip_reports_without_rejecting(client: TestClient) -> None:
    """TC-27 / FR-1.11: the skip policy reports duplicates without failing the file."""
    client.post("/api/leads", json=VALID_LEAD)
    csv_text = "company_name,email\nTechCorp Solutions,sarah@example.com\n"

    rejected = _upload(client, csv_text, duplicate_policy="reject").json()
    assert rejected["rejected"] == 1

    skipped = _upload(client, csv_text, duplicate_policy="skip").json()
    assert skipped["duplicates"] == 1
    assert skipped["rejected"] == 0
    assert skipped["inserted"] == 0


def test_tc28_duplicate_company_contact_flagged(client: TestClient) -> None:
    """TC-28 / FR-1.11: a matching company + contact pair is flagged for review."""
    client.post("/api/leads", json=VALID_LEAD)
    csv_text = (
        "company_name,contact_name,email\ntechcorp solutions,Sarah Johnson,other@example.com\n"
    )
    response = _upload(client, csv_text)
    body = response.json()
    assert body["duplicates"] == 1
    assert body["errors"][0]["reason"] == "duplicate_company_contact"


def test_tc29_import_report_shape(client: TestClient) -> None:
    """TC-29 / FR-1.12: the import report contains every documented counter."""
    response = _upload(client, VALID_CSV)
    body = response.json()
    for key in (
        "total_rows",
        "inserted",
        "updated",
        "duplicates",
        "rejected",
        "inserted_lead_ids",
        "errors",
    ):
        assert key in body


def test_tc30_non_csv_upload_rejected(client: TestClient) -> None:
    """FR-1.8: a non-CSV upload is refused before parsing."""
    response = client.post(
        "/api/leads/import",
        files={"file": ("leads.txt", io.BytesIO(b"company_name,email"), "text/plain")},
    )
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_tc31_update_existing_updates_the_record(client: TestClient) -> None:
    """TC-31 / FR-1.11: update_existing refreshes a matched record instead of duplicating it."""
    client.post("/api/leads", json=VALID_LEAD)

    csv_text = (
        "company_name,industry,contact_name,email,phone,lead_status,company_size,notes\n"
        "TechCorp Solutions,Software,Sarah Johnson,sarah@example.com,9876543210,"
        "Qualified,201-500,Met at the expo\n"
    )
    response = _upload(client, csv_text, update_existing="true")
    assert response.status_code == 200
    body = response.json()
    assert body["updated"] == 1
    assert body["inserted"] == 0
    assert body["duplicates"] == 0

    leads = client.get("/api/leads").json()
    assert leads["total"] == 1
    record = leads["items"][0]
    assert record["lead_status"] == "Qualified"
    assert record["company_size"] == "201-500"
    assert record["notes"] == "Met at the expo"


def test_tc32_update_existing_keeps_fields_absent_from_the_csv(client: TestClient) -> None:
    """TC-32: update_existing does not blank out fields the CSV does not carry."""
    client.post("/api/leads", json=VALID_LEAD)

    csv_text = "company_name,email,lead_status\nTechCorp Solutions,sarah@example.com,Contacted\n"
    response = _upload(client, csv_text, update_existing="true")
    assert response.json()["updated"] == 1

    record = client.get("/api/leads").json()["items"][0]
    assert record["lead_status"] == "Contacted"
    assert record["industry"] == "Software"
    assert record["contact_name"] == "Sarah Johnson"
    assert record["phone"] == "9876543210"


def test_tc33_update_existing_still_inserts_new_rows(client: TestClient) -> None:
    """TC-33: update_existing only affects duplicates; new rows are still inserted."""
    client.post("/api/leads", json=VALID_LEAD)

    csv_text = (
        "company_name,email\nTechCorp Solutions,sarah@example.com\nInnovate Labs,mark@example.com\n"
    )
    response = _upload(client, csv_text, update_existing="true")
    body = response.json()
    assert body["updated"] == 1
    assert body["inserted"] == 1
    assert client.get("/api/leads").json()["total"] == 2
