"""Explainable 0–100 prioritization, distinct from a model probability estimate."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import LeadScore
from app.ml.predict import predict
from app.services.intelligence_service import latest as latest_insight
from app.services.recommendation_service import recommend


def score_factors(lead, has_insight: bool):
    stage = {'New': 2, 'Contacted': 10, 'Qualified': 17, 'Converted': 20}.get(lead.lead_status, 0)
    values = [
        ('Industry relevance proxy', 10 if lead.industry else 0, 10, 'Industry provided; no product/market fit inferred'),
        ('Company size', 10 if lead.company_size else 0, 10, 'Size category documented' if lead.company_size else 'Size missing'),
        ('Contact completeness', (10 if lead.contact_name else 0) + (10 if lead.email else 0), 20, 'Named person and email recorded'),
        ('Engagement', round(lead.engagement_score * .25, 2), 25, f'Recorded engagement {lead.engagement_score}/100'),
        ('Lifecycle stage', stage, 20, f'Lead status: {lead.lead_status}'),
        ('Communication channel', 10 if (lead.email or lead.phone) else 0, 10, 'Email or telephone recorded'),
        ('Lead intelligence available', 5 if has_insight else 0, 5, 'Saved company analysis exists' if has_insight else 'No saved analysis yet'),
    ]
    factors = [{'name': name, 'points': points, 'max_points': maximum, 'explanation': why}
               for name, points, maximum, why in values]
    score = round(sum(x['points'] for x in factors), 2)
    band = 'Critical' if score >= 80 else 'High' if score >= 60 else 'Medium' if score >= 40 else 'Low'
    return score, band, factors


def compute(db: Session, lead):
    has_insight = latest_insight(db, lead.lead_id) is not None
    score, band, factors = score_factors(lead, has_insight)
    probability, mode, version = predict(lead)
    recommendation = recommend(lead, score, probability)
    entry = LeadScore(lead_id=lead.lead_id, score=score, priority_band=band, factors=factors,
                      conversion_probability=probability, prediction_mode=mode, model_version=version, **recommendation)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def latest(db: Session, lead_id: int):
    return db.scalars(select(LeadScore).where(LeadScore.lead_id == lead_id)
                      .order_by(LeadScore.created_at.desc(), LeadScore.score_id.desc())).first()
