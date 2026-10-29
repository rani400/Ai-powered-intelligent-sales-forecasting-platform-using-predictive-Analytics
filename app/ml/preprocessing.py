"""Shared feature contract for train-time and inference-time processing."""
import pandas as pd

CATEGORICAL = ['industry', 'company_size', 'lead_status']
NUMERIC = ['engagement_score', 'has_email', 'has_phone', 'has_contact']
FEATURES = CATEGORICAL + NUMERIC


def lead_features(lead):
    return pd.DataFrame([{
        'industry': (lead.industry or 'Unknown').strip().title(),
        'company_size': lead.company_size or 'Unknown',
        'lead_status': lead.lead_status,
        'engagement_score': float(lead.engagement_score),
        'has_email': int(bool(lead.email)),
        'has_phone': int(bool(lead.phone)),
        'has_contact': int(bool(lead.contact_name)),
    }], columns=FEATURES)
