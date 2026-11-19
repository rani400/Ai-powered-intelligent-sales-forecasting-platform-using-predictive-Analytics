"""CRM integration: Salesforce / HubSpot field mapping.

This module converts local lead records into CRM-ready payloads and back.
It performs mapping only; pushing to a live CRM requires credentials that
are intentionally not stored here.
"""
from typing import Any

LEAD_FIELDS = [
    "company_name", "industry", "contact_name", "contact_title", "email",
    "phone", "company_size", "annual_revenue", "engagement_score",
    "website_visits", "email_opens", "email_clicks", "budget_confirmed",
    "need_identified", "decision_maker", "lead_status", "notes",
]

SALESFORCE_FIELD_MAP: dict[str, str] = {
    "company_name": "Company",
    "industry": "Industry",
    "contact_name": "LastName",
    "contact_title": "Title",
    "email": "Email",
    "phone": "Phone",
    "company_size": "NumberOfEmployees",
    "annual_revenue": "AnnualRevenue",
    "engagement_score": "Engagement_Score__c",
    "website_visits": "Website_Visits__c",
    "email_opens": "Email_Opens__c",
    "email_clicks": "Email_Clicks__c",
    "budget_confirmed": "Budget_Confirmed__c",
    "need_identified": "Need_Identified__c",
    "decision_maker": "Decision_Maker__c",
    "lead_status": "Status",
    "notes": "Description",
}

HUBSPOT_FIELD_MAP: dict[str, str] = {
    "company_name": "company",
    "industry": "industry",
    "contact_name": "lastname",
    "contact_title": "jobtitle",
    "email": "email",
    "phone": "phone",
    "company_size": "numberofemployees",
    "annual_revenue": "annualrevenue",
    "engagement_score": "engagement_score",
    "website_visits": "website_visits",
    "email_opens": "email_opens",
    "email_clicks": "email_clicks",
    "budget_confirmed": "budget_confirmed",
    "need_identified": "need_identified",
    "decision_maker": "decision_maker",
    "lead_status": "hs_lead_status",
    "notes": "hs_content_membership_notes",
}

CRM_FIELD_MAPS: dict[str, dict[str, str]] = {
    "salesforce": SALESFORCE_FIELD_MAP,
    "hubspot": HUBSPOT_FIELD_MAP,
}


def _normalise_crm(crm: str) -> str:
    key = (crm or "").strip().lower()
    if key not in CRM_FIELD_MAPS:
        raise ValueError(f"Unsupported CRM '{crm}'. Use one of: {', '.join(CRM_FIELD_MAPS)}")
    return key


def get_field_mappings(crm: str | None = None) -> dict[str, Any]:
    if crm is None:
        return {
            "crms": list(CRM_FIELD_MAPS.keys()),
            "mappings": {name: {"lead_to_crm": m, "crm_to_lead": {v: k for k, v in m.items()}}
                         for name, m in CRM_FIELD_MAPS.items()},
        }
    key = _normalise_crm(crm)
    mapping = CRM_FIELD_MAPS[key]
    return {
        "crm": key,
        "lead_to_crm": mapping,
        "crm_to_lead": {v: k for k, v in mapping.items()},
        "lead_fields": LEAD_FIELDS,
    }


def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split(None, 1)
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def map_lead_to_crm(lead: dict[str, Any], crm: str) -> dict[str, Any]:
    key = _normalise_crm(crm)
    mapping = CRM_FIELD_MAPS[key]
    payload: dict[str, Any] = {}
    for lead_field, crm_field in mapping.items():
        value = lead.get(lead_field)
        if value is None:
            continue
        payload[crm_field] = value
    if key == "hubspot":
        first, last = _split_name(lead.get("contact_name") or "")
        if first:
            payload["firstname"] = first
        if last:
            payload["lastname"] = last
    return payload


def map_crm_to_lead(data: dict[str, Any], crm: str) -> dict[str, Any]:
    key = _normalise_crm(crm)
    mapping = CRM_FIELD_MAPS[key]
    reverse = {v: k for k, v in mapping.items()}
    lead: dict[str, Any] = {}
    for crm_field, value in (data or {}).items():
        lead_field = reverse.get(crm_field)
        if lead_field:
            lead[lead_field] = value
    if key == "hubspot":
        first = data.get("firstname") or ""
        last = data.get("lastname") or ""
        if first or last:
            lead["contact_name"] = f"{first} {last}".strip()
    return lead


def validate_field_mappings(crm: str) -> dict[str, Any]:
    key = _normalise_crm(crm)
    mapping = CRM_FIELD_MAPS[key]
    missing = [f for f in LEAD_FIELDS if f not in mapping]
    duplicates = [v for v in set(mapping.values()) if list(mapping.values()).count(v) > 1]
    return {
        "crm": key,
        "mapped_fields": len(mapping),
        "missing_lead_fields": missing,
        "duplicate_crm_targets": sorted(set(duplicates)),
        "valid": not missing and not duplicates,
    }
