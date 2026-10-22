"""Tests for the AI outreach generation service and draft storage."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.errors import UpstreamError
from app.services.outreach_generator import OutreachGenerator
from tests.conftest import VALID_LEAD


def test_tc60_request_validation(client: TestClient, created_lead: dict) -> None:
    """TC-60 / FR-4.1: an invalid tone, goal or length is rejected."""
    response = client.post(
        "/api/outreach/generate",
        json={
            "lead_id": created_lead["lead_id"],
            "product_or_service": "Lead intelligence platform",
            "tone": "sarcastic",
        },
    )
    assert response.status_code == 422
    assert any(issue["field"] == "tone" for issue in response.json()["errors"])


def test_tc61_prompt_contains_prospect_facts() -> None:
    """TC-61 / FR-4.2: the prompt is built from the supplied prospect data."""
    prompt = OutreachGenerator.build_prompt(
        company_name="TechCorp Solutions",
        contact_name="Sarah Johnson",
        industry="Software",
        product_or_service="SalesGenie AI",
        tone="professional",
        email_length="short",
        communication_goal="meeting",
    )
    assert "TechCorp Solutions" in prompt.user_prompt
    assert "Sarah Johnson" in prompt.user_prompt
    assert "SalesGenie AI" in prompt.user_prompt
    assert "SUBJECT:" in prompt.system_prompt
    assert "BODY:" in prompt.system_prompt


def test_tc62_provider_response_is_parsed() -> None:
    """TC-62 / FR-4.3: a SUBJECT/BODY response is parsed into its two parts."""
    raw = "SUBJECT: Scaling lead ops at TechCorp\n\nBODY: Hi Sarah,\n\nBody text here."
    subject, body = OutreachGenerator.parse_response(raw)
    assert subject == "Scaling lead ops at TechCorp"
    assert body.startswith("Hi Sarah,")


def test_tc63_mock_mode_is_clearly_labelled(client: TestClient, created_lead: dict) -> None:
    """TC-63 / FR-4.4: with no provider configured the draft is labelled as mock."""
    response = client.post(
        "/api/outreach/generate",
        json={
            "lead_id": created_lead["lead_id"],
            "product_or_service": "SalesGenie AI lead intelligence platform",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_mock"] is True
    assert body["provider"] == "mock"
    assert "mock mode" in (body["notes"] or "").lower()
    assert body["email_subject"]
    assert body["email_content"]


def test_tc64_provider_timeout_is_handled() -> None:
    """TC-64 / FR-4.5: a provider timeout raises a clean upstream error."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    generator = OutreachGenerator(
        api_key="test-key", transport=httpx.MockTransport(handler), max_retries=0
    )
    with pytest.raises(UpstreamError) as excinfo:
        generator.generate(
            company_name="TechCorp Solutions",
            contact_name="Sarah Johnson",
            industry="Software",
            product_or_service="SalesGenie AI",
        )
    assert "timed out" in excinfo.value.detail.lower()


def test_tc65_provider_error_is_handled() -> None:
    """TC-65 / FR-4.5: a provider HTTP error is surfaced as a 502-style domain error."""
    generator = OutreachGenerator(
        api_key="test-key",
        transport=httpx.MockTransport(lambda request: httpx.Response(500, json={"error": "boom"})),
        max_retries=0,
    )
    with pytest.raises(UpstreamError):
        generator.generate(
            company_name="TechCorp Solutions",
            contact_name=None,
            industry="Software",
            product_or_service="SalesGenie AI",
        )


def test_tc66_empty_provider_response_is_handled() -> None:
    """TC-66 / FR-4.5: an empty provider response is rejected with a clear message."""
    generator = OutreachGenerator(
        api_key="test-key",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"choices": [{"message": {"content": "   "}}]}
            )
        ),
        max_retries=0,
    )
    with pytest.raises(UpstreamError) as excinfo:
        generator.generate(
            company_name="TechCorp Solutions",
            contact_name=None,
            industry="Software",
            product_or_service="SalesGenie AI",
        )
    assert "empty" in excinfo.value.detail.lower()


def test_tc67_draft_is_stored_as_draft(client: TestClient, created_lead: dict) -> None:
    """TC-67 / FR-4.6 / FR-4.8: drafts are stored and never marked as sent."""
    response = client.post(
        "/api/outreach/generate",
        json={
            "lead_id": created_lead["lead_id"],
            "product_or_service": "SalesGenie AI lead intelligence platform",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["campaign_status"] == "draft"

    stored = client.get(f"/api/leads/{created_lead['lead_id']}/outreach").json()
    assert stored["total"] == 1
    assert stored["items"][0]["campaign_status"] == "draft"
    assert stored["items"][0]["email_subject"] == body["email_subject"]


def test_tc68_drafts_can_be_retrieved(client: TestClient, created_lead: dict) -> None:
    """TC-68 / FR-4.7: stored drafts are retrievable by lead and in the global list."""
    for goal in ("product_introduction", "meeting", "follow_up"):
        client.post(
            "/api/outreach/generate",
            json={
                "lead_id": created_lead["lead_id"],
                "product_or_service": "SalesGenie AI lead intelligence platform",
                "communication_goal": goal,
            },
        )

    per_lead = client.get(f"/api/leads/{created_lead['lead_id']}/outreach").json()
    assert per_lead["total"] == 3

    global_list = client.get("/api/outreach").json()
    assert global_list["total"] == 3


def test_tc69_tone_and_length_variants(client: TestClient, created_lead: dict) -> None:
    """TC-69 / FR-4.9: tone and length options change the generated draft."""
    base = {
        "lead_id": created_lead["lead_id"],
        "product_or_service": "SalesGenie AI lead intelligence platform",
    }
    professional = client.post(
        "/api/outreach/generate", json={**base, "tone": "professional", "email_length": "short"}
    ).json()
    friendly = client.post(
        "/api/outreach/generate", json={**base, "tone": "friendly", "email_length": "short"}
    ).json()
    detailed = client.post(
        "/api/outreach/generate",
        json={**base, "tone": "professional", "email_length": "detailed"},
    ).json()

    assert professional["email_content"] != friendly["email_content"]
    assert len(detailed["email_content"]) > len(professional["email_content"])
    assert friendly["tone"] == "friendly"
    assert detailed["email_length"] == "detailed"


def test_tc70_generate_for_unknown_lead_returns_404(client: TestClient) -> None:
    """FR-4.1: an unknown lead id produces a 404."""
    response = client.post(
        "/api/outreach/generate",
        json={"lead_id": 9999, "product_or_service": "SalesGenie AI"},
    )
    assert response.status_code == 404


def test_tc71_provider_error_returns_502(client: TestClient, created_lead: dict) -> None:
    """FR-4.5: a provider failure is returned as 502, not a server crash."""
    original = OutreachGenerator.__init__

    def broken_init(self, *args, **kwargs):  # noqa: ANN001, ANN202
        original(
            self,
            api_key="test-key",
            transport=httpx.MockTransport(lambda request: httpx.Response(503)),
            max_retries=0,
        )

    OutreachGenerator.__init__ = broken_init  # type: ignore[method-assign]
    try:
        response = client.post(
            "/api/outreach/generate",
            json={
                "lead_id": created_lead["lead_id"],
                "product_or_service": "SalesGenie AI lead intelligence platform",
            },
        )
    finally:
        OutreachGenerator.__init__ = original  # type: ignore[method-assign]

    assert response.status_code == 502
    assert response.json()["detail"]


def test_tc72_draft_uses_stored_lead_data(client: TestClient) -> None:
    """FR-4.1: stored lead data is used when the request does not override it."""
    client.post("/api/leads", json=VALID_LEAD)
    created = client.get("/api/leads").json()["items"][0]

    draft = client.post(
        "/api/outreach/generate",
        json={"lead_id": created["lead_id"], "product_or_service": "SalesGenie AI"},
    ).json()

    assert "TechCorp Solutions" in draft["email_subject"] or "Sarah Johnson" in draft["email_content"]
