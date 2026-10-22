"""Lead intelligence: company analysis, qualification scoring and insight generation.

This module covers Module 2 (Lead Intelligence & Company Analysis) and the Module 4 baseline
(rule-based qualification score).

Design rules for this service:

1. Every statement is derived from a field stored on the lead record, or from a **sector-level**
   reference table. Sector statements are phrased as hypotheses about the sector, never as facts
   about the specific company.
2. When a field is missing, the gap is reported in ``information_gaps`` instead of being filled
   with an invented value.
3. The analysis is persisted in ``company_insights`` and the score in ``lead_scores`` so both can
   be audited and compared over time.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company_insight import CompanyInsight
from app.models.lead import Lead, LeadStatus
from app.models.lead_score import LeadScore
from app.schemas.lead_schema import (
    CompanyProfile,
    LeadInsightResponse,
    QualificationScore,
    ScoreFactor,
)

# ---------------------------------------------------------------------------
# Qualification scoring (Module 4 baseline)
# ---------------------------------------------------------------------------
#
# The score is a transparent, deterministic heuristic over the fields stored on a lead record.
# It is a **prioritisation aid**, not a trained conversion-probability model: it produces no
# claim about how likely a lead is to buy. Every factor, weight and raw value is returned with
# the score so a sales manager can see exactly why a number was produced.

METHODOLOGY = "rule_based_v1"

#: Industries that the current sales motion is configured to target.
TARGET_INDUSTRIES = {
    "software",
    "technology",
    "saas",
    "cloud computing",
    "analytics",
    "data",
    "artificial intelligence",
    "machine learning",
    "fintech",
    "financial technology",
    "healthcare tech",
    "ecommerce",
    "e-commerce",
    "cybersecurity",
    "devops",
    "enterprise software",
}

#: How well a recorded company-size band fits the current motion.
COMPANY_SIZE_FIT = {
    "1-10": 0.30,
    "11-50": 0.40,
    "51-200": 0.70,
    "201-500": 0.90,
    "501-1000": 1.00,
    "1000+": 1.00,
}

#: Engagement stage implied by the recorded lead status.
STATUS_FIT = {
    LeadStatus.CONVERTED.value: 1.00,
    LeadStatus.QUALIFIED.value: 0.85,
    LeadStatus.CONTACTED.value: 0.70,
    LeadStatus.NEW.value: 0.50,
    LeadStatus.UNQUALIFIED.value: 0.20,
    LeadStatus.LOST.value: 0.10,
}

#: Fields whose presence indicates a complete prospect record.
COMPLETENESS_FIELDS = ("contact_name", "email", "phone", "industry", "company_size")

WEIGHTS = {
    "Industry relevance": 30.0,
    "Company size signal": 20.0,
    "Contact data completeness": 25.0,
    "Engagement stage": 20.0,
    "Reachable channel": 5.0,
}


@dataclass(frozen=True)
class ScoreFactorResult:
    """One weighted contributor to the qualification score."""

    name: str
    weight: float
    raw_value: float
    points_awarded: float
    explanation: str

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-serialisable representation of the factor."""
        return asdict(self)


@dataclass(frozen=True)
class ScoreResult:
    """A complete score with its audit trail."""

    score: float
    band: str
    factors: list[ScoreFactorResult]
    methodology: str = METHODOLOGY

    @property
    def factors_as_dicts(self) -> list[dict[str, object]]:
        """Return the factor list as plain dictionaries."""
        return [factor.to_dict() for factor in self.factors]

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-serialisable representation of the score."""
        return {
            "score": self.score,
            "band": self.band,
            "factors": self.factors_as_dicts,
            "methodology": self.methodology,
        }


def _band_for(score: float) -> str:
    """Map a numeric score to its qualitative band."""
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def _industry_factor(industry: str | None) -> ScoreFactorResult:
    """Score how well the recorded industry matches the target list."""
    weight = WEIGHTS["Industry relevance"]
    if not industry:
        return ScoreFactorResult(
            name="Industry relevance",
            weight=weight,
            raw_value=0.0,
            points_awarded=0.0,
            explanation="No industry recorded, so sector fit cannot be assessed.",
        )

    key = industry.strip().lower()
    if key in TARGET_INDUSTRIES:
        raw = 1.0
        explanation = f"'{industry}' is a configured target industry."
    else:
        matched = sorted(target for target in TARGET_INDUSTRIES if target in key or key in target)
        if matched:
            raw = 0.8
            explanation = f"'{industry}' closely matches target industry '{matched[0]}'."
        else:
            raw = 0.4
            explanation = f"'{industry}' is not in the configured target industry list."
    return ScoreFactorResult(
        name="Industry relevance",
        weight=weight,
        raw_value=raw,
        points_awarded=round(weight * raw, 2),
        explanation=explanation,
    )


def _company_size_factor(company_size: str | None) -> ScoreFactorResult:
    """Score the recorded company-size band."""
    weight = WEIGHTS["Company size signal"]
    if not company_size:
        return ScoreFactorResult(
            name="Company size signal",
            weight=weight,
            raw_value=0.0,
            points_awarded=0.0,
            explanation="No company size recorded, so account fit cannot be assessed.",
        )

    key = company_size.strip().lower()
    raw = COMPANY_SIZE_FIT.get(key)
    if raw is None:
        raw = 0.5
        explanation = (
            f"Company size '{company_size}' is not a recognised band; neutral score applied."
        )
    else:
        explanation = f"Company size band '{company_size}' maps to fit factor {raw:.2f}."
    return ScoreFactorResult(
        name="Company size signal",
        weight=weight,
        raw_value=raw,
        points_awarded=round(weight * raw, 2),
        explanation=explanation,
    )


def _completeness_factor(lead: Lead) -> ScoreFactorResult:
    """Score how complete the prospect record is."""
    weight = WEIGHTS["Contact data completeness"]
    present = [name for name in COMPLETENESS_FIELDS if getattr(lead, name, None)]
    raw = len(present) / len(COMPLETENESS_FIELDS)
    explanation = f"{len(present)} of {len(COMPLETENESS_FIELDS)} key fields present."
    return ScoreFactorResult(
        name="Contact data completeness",
        weight=weight,
        raw_value=round(raw, 4),
        points_awarded=round(weight * raw, 2),
        explanation=explanation,
    )


def _engagement_factor(lead_status: str) -> ScoreFactorResult:
    """Score the engagement stage implied by the lead status."""
    weight = WEIGHTS["Engagement stage"]
    raw = STATUS_FIT.get(lead_status, 0.5)
    explanation = f"Status '{lead_status}' indicates engagement stage factor {raw:.2f}."
    return ScoreFactorResult(
        name="Engagement stage",
        weight=weight,
        raw_value=raw,
        points_awarded=round(weight * raw, 2),
        explanation=explanation,
    )


def _reachability_factor(lead: Lead) -> ScoreFactorResult:
    """Score whether there is any usable way to reach the contact."""
    weight = WEIGHTS["Reachable channel"]
    if lead.email:
        raw = 1.0
        explanation = "A direct email address is recorded."
    elif lead.phone:
        raw = 0.6
        explanation = "Only a phone number is recorded; email outreach is not yet possible."
    else:
        raw = 0.0
        explanation = "No email or phone recorded, so the contact is not reachable yet."
    return ScoreFactorResult(
        name="Reachable channel",
        weight=weight,
        raw_value=raw,
        points_awarded=round(weight * raw, 2),
        explanation=explanation,
    )


def calculate_qualification_score(lead: Lead) -> ScoreResult:
    """Compute the qualification score for a lead.

    The function is deterministic: the same lead record always produces the same score.
    """
    factors = [
        _industry_factor(lead.industry),
        _company_size_factor(lead.company_size),
        _completeness_factor(lead),
        _engagement_factor(lead.lead_status),
        _reachability_factor(lead),
    ]
    total = round(sum(factor.points_awarded for factor in factors), 2)
    total = max(0.0, min(100.0, total))
    return ScoreResult(score=total, band=_band_for(total), factors=factors)


# ---------------------------------------------------------------------------
# Company analysis (Module 2)
# ---------------------------------------------------------------------------

#: Sector-level reference data used to phrase needs and opportunities.
#:
#: The entries describe *sectors*, not specific companies. They are used to phrase hypotheses
#: that a salesperson can validate, never asserted as facts about the prospect.
INDUSTRY_REFERENCE: dict[str, dict[str, list[str]]] = {
    "software": {
        "needs": [
            "Shorten the sales cycle for inbound and outbound prospect data handling",
            "Keep prospect records consistent across multiple tools and reps",
            "Give non-technical stakeholders a readable view of pipeline activity",
        ],
        "opportunities": [
            "Prospect database with automated validation and de-duplication",
            "Lead intelligence that scores and explains each record",
            "AI-drafted first-touch outreach with a review step",
        ],
        "triggers": [
            "team growth beyond a handful of reps",
            "manual spreadsheet prospect lists",
            "slow follow-up on inbound enquiries",
        ],
    },
    "technology": {
        "needs": [
            "Reduce administrative time spent on lead research",
            "Standardise qualification across the sales team",
            "Capture prospect knowledge that currently lives in rep notebooks",
        ],
        "opportunities": [
            "Automated company research and insight generation",
            "Centralised prospect database with import pipelines",
            "Sales analytics that show where effort is spent",
        ],
        "triggers": ["new market expansion", "hiring sales roles", "new CRM rollout"],
    },
    "cloud computing": {
        "needs": [
            "Qualify inbound cloud enquiries before a demo is scheduled",
            "Connect technical buying committees to a single record",
        ],
        "opportunities": [
            "Lead scoring with explainable factors",
            "Outreach drafting that speaks to infrastructure teams",
            "Duplicate suppression across partner-sourced leads",
        ],
        "triggers": ["cost optimisation programmes", "multi-cloud adoption", "migration projects"],
    },
    "analytics": {
        "needs": [
            "Turn scattered prospect lists into a usable dataset",
            "Make pipeline quality visible to leadership",
        ],
        "opportunities": [
            "CSV ingestion with validation and duplicate reporting",
            "Qualification scores with visible reasoning",
            "Per-lead insight records for audit",
        ],
        "triggers": ["data consolidation projects", "reporting requests from leadership"],
    },
    "default": {
        "needs": [
            "A single source of truth for prospect records",
            "A repeatable way to prioritise which prospects to contact first",
            "Less manual work preparing first-touch outreach",
        ],
        "opportunities": [
            "Centralised prospect database with CSV import",
            "Transparent lead scoring and prioritisation",
            "AI-assisted outreach drafting with human review",
        ],
        "triggers": ["process review", "tool consolidation", "quota pressure"],
    },
}


def _reference_for(industry: str | None) -> tuple[str, dict[str, list[str]]]:
    """Return the sector reference bucket and its key for an industry value."""
    if not industry:
        return "default", INDUSTRY_REFERENCE["default"]
    key = industry.strip().lower()
    if key in INDUSTRY_REFERENCE:
        return key, INDUSTRY_REFERENCE[key]
    for candidate, payload in INDUSTRY_REFERENCE.items():
        if candidate != "default" and (candidate in key or key in candidate):
            return candidate, payload
    return "default", INDUSTRY_REFERENCE["default"]


def build_company_profile(lead: Lead) -> CompanyProfile:
    """Build the stored-fact profile used to anchor the analysis."""
    present = sum(1 for name in COMPLETENESS_FIELDS if getattr(lead, name, None))
    return CompanyProfile(
        company_name=lead.company_name,
        industry=lead.industry,
        contact_name=lead.contact_name,
        email=lead.email,
        lead_status=lead.lead_status,
        data_completeness=round(present / len(COMPLETENESS_FIELDS), 4),
    )


def build_information_gaps(lead: Lead) -> list[str]:
    """List the facts that are missing and would improve qualification."""
    gaps: list[str] = []
    if not lead.industry:
        gaps.append("Industry not recorded - sector-specific analysis is generic.")
    if not lead.company_size:
        gaps.append("Company size not recorded - account-fit weighting cannot be applied.")
    if not lead.contact_name:
        gaps.append("Contact name not recorded - outreach cannot be personalised by name.")
    if not lead.email:
        gaps.append("Email not recorded - the contact cannot be reached by email.")
    if not lead.phone:
        gaps.append("Phone not recorded - no secondary outreach channel is available.")
    if not lead.notes:
        gaps.append("No engagement notes stored - intent signals are unknown.")
    if not gaps:
        gaps.append("No gaps detected: all core prospect fields are populated.")
    return gaps


def build_key_insights(lead: Lead, profile: CompanyProfile) -> list[str]:
    """Derive statements that are strictly grounded in the stored record."""
    insights: list[str] = []
    bucket, reference = _reference_for(lead.industry)

    if lead.industry:
        insights.append(
            f"Recorded industry '{lead.industry}' maps to the '{bucket}' sector reference."
        )
        triggers = reference.get("triggers", [])
        if triggers:
            insights.append(
                f"Sector-level buying triggers for '{bucket}': " + "; ".join(triggers) + "."
            )
    else:
        insights.append(
            "No industry recorded, so the analysis falls back to generic prospecting patterns."
        )

    insights.append(
        f"Record completeness is {profile.data_completeness * 100:.0f}% "
        f"across contact name, email, phone, industry and company size."
    )
    insights.append(f"Current pipeline status for this record is '{lead.lead_status}'.")

    if lead.contact_name and lead.email:
        insights.append(
            f"A named contact ({lead.contact_name}) with a working email format is stored, "
            "so personalised outreach is possible."
        )
    elif lead.email:
        insights.append(
            "An email address is stored but the contact name is missing, "
            "so the greeting will be generic."
        )
    else:
        insights.append(
            "No direct channel is stored, so this record needs enrichment before outreach."
        )

    return insights


def generate_insight(lead: Lead) -> LeadInsightResponse:
    """Run the full company analysis for a lead without persisting it."""
    profile = build_company_profile(lead)
    _, reference = _reference_for(lead.industry)
    score = calculate_qualification_score(lead)

    return LeadInsightResponse(
        lead_id=lead.lead_id,
        generated_at=datetime.now(UTC),
        company_profile=profile,
        qualification_score=QualificationScore(
            score=score.score,
            band=score.band,
            factors=[ScoreFactor(**factor.to_dict()) for factor in score.factors],
            methodology=score.methodology,
        ),
        business_needs=list(reference.get("needs", [])),
        opportunities=list(reference.get("opportunities", [])),
        key_insights=build_key_insights(lead, profile),
        information_gaps=build_information_gaps(lead),
        is_cached=False,
    )


def persist_insight(db: Session, lead: Lead, insight: LeadInsightResponse) -> CompanyInsight:
    """Store the analysis and its score in the database."""
    record = CompanyInsight(
        lead_id=lead.lead_id,
        company_name=lead.company_name,
        industry=lead.industry,
        summary=(
            f"{lead.company_name}"
            + (f" ({lead.industry})" if lead.industry else "")
            + f" - qualification score {insight.qualification_score.score:.0f}"
            f" ({insight.qualification_score.band}). "
            f"Record completeness {insight.company_profile.data_completeness * 100:.0f}%."
        ),
        business_needs=json.dumps(insight.business_needs),
        opportunities=json.dumps(insight.opportunities),
        key_insights=json.dumps(insight.key_insights),
        information_gaps=json.dumps(insight.information_gaps),
        qualification_score=insight.qualification_score.score,
    )
    db.add(record)

    db.add(
        LeadScore(
            lead_id=lead.lead_id,
            score=insight.qualification_score.score,
            band=insight.qualification_score.band,
            factors=json.dumps(
                [factor.model_dump() for factor in insight.qualification_score.factors]
            ),
            methodology=insight.qualification_score.methodology,
        )
    )
    db.commit()
    db.refresh(record)
    return record


def latest_insight_record(db: Session, lead_id: int) -> CompanyInsight | None:
    """Return the most recent stored insight for a lead, if any."""
    return db.execute(
        select(CompanyInsight)
        .where(CompanyInsight.lead_id == lead_id)
        .order_by(CompanyInsight.created_at.desc(), CompanyInsight.insight_id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _record_to_response(db: Session, record: CompanyInsight, lead: Lead) -> LeadInsightResponse:
    """Rebuild an API response from a stored insight record."""
    score_row = db.execute(
        select(LeadScore)
        .where(LeadScore.lead_id == lead.lead_id)
        .order_by(LeadScore.created_at.desc(), LeadScore.score_id.desc())
        .limit(1)
    ).scalar_one_or_none()

    factors: list[ScoreFactor] = []
    score_value = record.qualification_score or 0.0
    band = "Low"
    methodology = METHODOLOGY
    if score_row is not None:
        score_value = score_row.score
        band = score_row.band
        methodology = score_row.methodology
        try:
            factors = [ScoreFactor(**item) for item in json.loads(score_row.factors or "[]")]
        except (ValueError, TypeError):  # pragma: no cover - defensive
            factors = []

    return LeadInsightResponse(
        lead_id=lead.lead_id,
        generated_at=record.created_at,
        company_profile=build_company_profile(lead),
        qualification_score=QualificationScore(
            score=score_value,
            band=band,
            factors=factors,
            methodology=methodology,
        ),
        business_needs=json.loads(record.business_needs or "[]"),
        opportunities=json.loads(record.opportunities or "[]"),
        key_insights=json.loads(record.key_insights or "[]"),
        information_gaps=json.loads(record.information_gaps or "[]"),
        is_cached=True,
    )


def get_or_generate_insight(db: Session, lead: Lead, refresh: bool = False) -> LeadInsightResponse:
    """Return the cached insight for a lead or generate and store a fresh one."""
    if not refresh:
        cached = latest_insight_record(db, lead.lead_id)
        if cached is not None:
            return _record_to_response(db, cached, lead)

    insight = generate_insight(lead)
    persist_insight(db, lead, insight)
    return insight


__all__ = [
    "COMPANY_SIZE_FIT",
    "COMPLETENESS_FIELDS",
    "INDUSTRY_REFERENCE",
    "METHODOLOGY",
    "STATUS_FIT",
    "TARGET_INDUSTRIES",
    "WEIGHTS",
    "QualificationScore",
    "ScoreFactor",
    "ScoreFactorResult",
    "ScoreResult",
    "build_company_profile",
    "build_information_gaps",
    "build_key_insights",
    "calculate_qualification_score",
    "generate_insight",
    "get_or_generate_insight",
    "latest_insight_record",
    "persist_insight",
]
