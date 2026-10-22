"""Tests for the lead intelligence and qualification scoring services."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.lead import Lead, LeadStatus
from app.services.lead_intelligence import generate_insight
from app.services.lead_intelligence import WEIGHTS, calculate_qualification_score
from tests.conftest import VALID_LEAD


def _lead(**overrides) -> Lead:
    """Build an unsaved lead object for service-level tests."""
    values = {
        "lead_id": 1,
        "company_name": "TechCorp Solutions",
        "industry": "Software",
        "contact_name": "Sarah Johnson",
        "email": "sarah@example.com",
        "phone": "9876543210",
        "lead_status": LeadStatus.NEW.value,
        "company_size": "51-200",
    }
    values.update(overrides)
    return Lead(**values)


def test_tc40_insight_profile_uses_stored_fields() -> None:
    """TC-40 / FR-2.1: the company profile is built from stored values only."""
    insight = generate_insight(_lead())
    profile = insight.company_profile
    assert profile.company_name == "TechCorp Solutions"
    assert profile.industry == "Software"
    assert profile.contact_name == "Sarah Johnson"
    assert profile.lead_status == "New"
    assert 0.0 <= profile.data_completeness <= 1.0


def test_tc41_business_needs_and_opportunities_present() -> None:
    """TC-41 / FR-2.2: sector needs and opportunities are produced."""
    insight = generate_insight(_lead())
    assert insight.business_needs
    assert insight.opportunities
    assert all(isinstance(item, str) and item for item in insight.business_needs)
    assert all(isinstance(item, str) and item for item in insight.opportunities)


def test_tc42_information_gaps_reported() -> None:
    """TC-42 / FR-2.3: missing fields are reported as gaps rather than invented."""
    insight = generate_insight(
        _lead(industry=None, company_size=None, contact_name=None, phone=None, notes=None)
    )
    gaps = " ".join(insight.information_gaps).lower()
    assert "industry" in gaps
    assert "company size" in gaps
    assert "contact name" in gaps
    assert "phone" in gaps


def test_tc43_insight_is_persisted_with_relationships(client: TestClient) -> None:
    """TC-43 / FR-2.4 / NFR-2: analysis and score rows are stored against the lead."""
    created = client.post("/api/leads", json=VALID_LEAD).json()
    lead_id = created["lead_id"]

    response = client.get(f"/api/leads/{lead_id}/insights")
    assert response.status_code == 200
    body = response.json()
    assert body["lead_id"] == lead_id
    assert body["is_cached"] is False
    assert body["qualification_score"]["score"] >= 0

    cached = client.get(f"/api/leads/{lead_id}/insights").json()
    assert cached["is_cached"] is True

    refreshed = client.get(f"/api/leads/{lead_id}/insights", params={"refresh": "true"}).json()
    assert refreshed["is_cached"] is False


def test_tc44_no_invented_company_facts() -> None:
    """TC-44 / FR-2.5: no revenue, headcount or funding claims are invented."""
    insight = generate_insight(_lead())
    text = " ".join(insight.key_insights).lower()
    for forbidden in ("revenue", "funding", "raised", "valuation", "employees"):
        assert forbidden not in text


def test_tc45_insights_endpoint_returns_payload(client: TestClient) -> None:
    """TC-45 / FR-2.6: the insights endpoint returns the documented shape."""
    created = client.post("/api/leads", json=VALID_LEAD).json()
    body = client.get(f"/api/leads/{created['lead_id']}/insights").json()

    assert set(body) >= {
        "lead_id",
        "generated_at",
        "company_profile",
        "qualification_score",
        "business_needs",
        "opportunities",
        "key_insights",
        "information_gaps",
    }
    assert body["qualification_score"]["methodology"] == "rule_based_v1"
    assert "not a trained conversion-probability model" in body["qualification_score"]["disclaimer"]


def test_tc46_insights_for_unknown_lead_returns_404(client: TestClient) -> None:
    """TC-46: an unknown lead id produces a 404."""
    assert client.get("/api/leads/9999/insights").status_code == 404


def test_tc50_score_is_normalised_and_documented() -> None:
    """TC-50 / FR-3.1: the score is a 0-100 value built from the documented factors."""
    score = calculate_qualification_score(_lead())
    assert 0.0 <= score.score <= 100.0
    assert score.band in {"Low", "Medium", "High"}
    assert sum(factor.weight for factor in score.factors) == sum(WEIGHTS.values())
    assert sum(factor.points_awarded for factor in score.factors) == score.score


def test_tc51_factors_include_explanations() -> None:
    """TC-51 / FR-3.2: every factor explains itself."""
    score = calculate_qualification_score(_lead())
    for factor in score.factors:
        assert factor.explanation
        assert factor.points_awarded <= factor.weight


def test_tc52_empty_record_scores_low() -> None:
    """TC-52: a record with no data scores at the bottom of the range."""
    score = calculate_qualification_score(
        _lead(industry=None, company_size=None, contact_name=None, email=None, phone=None)
    )
    assert score.score < 20.0
    assert score.band == "Low"


def test_tc53_score_is_deterministic() -> None:
    """TC-53 / FR-3.5: identical input always produces an identical score."""
    first = calculate_qualification_score(_lead())
    second = calculate_qualification_score(_lead())
    assert first.score == second.score
    assert first.band == second.band


def test_tc54_score_rows_are_recorded(client: TestClient) -> None:
    """FR-3.3: every score run is stored in lead_scores."""
    from sqlalchemy import func, select

    from app.database import get_db
    from app.models.lead_score import LeadScore

    created = client.post("/api/leads", json=VALID_LEAD).json()
    client.get(f"/api/leads/{created['lead_id']}/insights")
    client.get(f"/api/leads/{created['lead_id']}/insights", params={"refresh": "true"})

    db_gen = get_db()
    db = next(db_gen)
    try:
        count = db.execute(
            select(func.count()).select_from(LeadScore).where(LeadScore.lead_id == created["lead_id"])
        ).scalar_one()
    finally:
        db_gen.close()
    assert count == 2


def test_tc55_score_stored_in_dashboard_stats(client: TestClient) -> None:
    """FR-5.1: the dashboard counters reflect the stored score."""
    created = client.post("/api/leads", json=VALID_LEAD).json()
    client.get(f"/api/leads/{created['lead_id']}/insights")

    stats = client.get("/api/leads/stats").json()
    assert stats["scored_leads"] == 1
    assert stats["average_score"] is not None
    assert 0 <= stats["average_score"] <= 100
