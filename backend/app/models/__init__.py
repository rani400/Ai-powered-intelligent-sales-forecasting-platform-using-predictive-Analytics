"""ORM model package.

Importing this package registers every model on the shared declarative metadata so that
``Base.metadata.create_all`` and the migration runner see the complete schema.
"""

from app.models.company_insight import CompanyInsight
from app.models.extended import (
    CRMSyncLog,
    SalesAnalyticsSnapshot,
    SalesInteraction,
    User,
)
from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.lead_score import LeadScore
from app.models.outreach_campaign import CampaignStatus, OutreachCampaign

__all__ = [
    "CRMSyncLog",
    "CampaignStatus",
    "CompanyInsight",
    "Lead",
    "LeadScore",
    "LeadSource",
    "LeadStatus",
    "OutreachCampaign",
    "SalesAnalyticsSnapshot",
    "SalesInteraction",
    "User",
]
