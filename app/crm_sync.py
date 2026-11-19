"""CRM sync logic: contacts, activities, deal stages, and sync logs.

Orchestrates mapping a local lead/activity into CRM payloads and records every
attempt in the `crm_sync_logs` table. If CRM credentials are configured in the
environment a live HTTP push is attempted; otherwise the payload is prepared and
logged as a dry run ("mapped").
"""
from __future__ import annotations

import json
import os
from typing import Any

import requests

from .crm import _normalise_crm, map_lead_to_crm
from .database import connect

SALESFORCE_STAGES = {
    "New": "Prospecting",
    "Contacted": "Prospecting",
    "Qualified": "Qualification",
    "Proposal": "Proposal/Price Quote",
    "Negotiation": "Negotiation/Review",
    "Won": "Closed Won",
    "Lost": "Closed Lost",
}

HUBSPOT_STAGES = {
    "New": "appointmentscheduled",
    "Contacted": "qualifiedtobuy",
    "Qualified": "presentationscheduled",
    "Proposal": "decisionmakerboughtin",
    "Negotiation": "contractsent",
    "Won": "closedwon",
    "Lost": "closedlost",
}

DEAL_STAGE_MAPS = {"salesforce": SALESFORCE_STAGES, "hubspot": HUBSPOT_STAGES}

SALESFORCE_ACTIVITY_TYPES = {"call": "Call", "email": "Email", "meeting": "Meeting", "note": "Note"}
HUBSPOT_ACTIVITY_TYPES = {"call": "CALL", "email": "EMAIL", "meeting": "MEETING", "note": "NOTE"}
ACTIVITY_TYPE_MAPS = {"salesforce": SALESFORCE_ACTIVITY_TYPES, "hubspot": HUBSPOT_ACTIVITY_TYPES}


def get_deal_stages(crm: str | None = None) -> dict[str, Any]:
    if crm is None:
        return {"crms": list(DEAL_STAGE_MAPS), "stages": DEAL_STAGE_MAPS}
    key = _normalise_crm(crm)
    return {"crm": key, "stages": DEAL_STAGE_MAPS[key]}


def map_deal_stage(lead_status: str, crm: str) -> str:
    key = _normalise_crm(crm)
    return DEAL_STAGE_MAPS[key].get(lead_status or "New", DEAL_STAGE_MAPS[key].get("New"))


def map_activity_type(activity_type: str, crm: str) -> str:
    key = _normalise_crm(crm)
    return ACTIVITY_TYPE_MAPS[key].get((activity_type or "note").lower(), ACTIVITY_TYPE_MAPS[key]["note"])


def log_sync(crm: str, entity_type: str, entity_id: int | None, direction: str,
             status: str, message: str, payload: Any = None, remote_id: str | None = None) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO crm_sync_logs
               (crm, entity_type, entity_id, direction, status, message, payload, remote_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (crm, entity_type, entity_id, direction, status, message,
             json.dumps(payload) if payload is not None else None, remote_id),
        )
        conn.commit()
        return cur.lastrowid


def get_sync_logs(crm: str | None = None, entity_type: str | None = None,
                  status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    sql = "SELECT * FROM crm_sync_logs WHERE 1=1"
    params: list[Any] = []
    if crm:
        sql += " AND crm = ?"; params.append(crm)
    if entity_type:
        sql += " AND entity_type = ?"; params.append(entity_type)
    if status:
        sql += " AND status = ?"; params.append(status)
    sql += " ORDER BY id DESC LIMIT ?"; params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _creds(crm: str) -> dict[str, str]:
    return {
        "salesforce_url": os.getenv("SALESFORCE_INSTANCE_URL", ""),
        "salesforce_token": os.getenv("SALESFORCE_ACCESS_TOKEN", ""),
        "hubspot_token": os.getenv("HUBSPOT_ACCESS_TOKEN", ""),
    }


def _push_live(crm: str, object_type: str, payload: dict[str, Any]) -> tuple[str | None, str]:
    """Attempt a real CRM API push. Returns (remote_id, message). Raises on error."""
    creds = _creds(crm)
    if crm == "salesforce":
        if not (creds["salesforce_url"] and creds["salesforce_token"]):
            return None, "Salesforce credentials not configured; payload prepared only."
        sobject = {"contact": "Lead", "deal": "Opportunity", "activity": "Task"}[object_type]
        url = creds["salesforce_url"].rstrip("/") + f"/services/data/v60.0/sobjects/{sobject}/"
        r = requests.post(url, headers={"Authorization": f"Bearer {creds['salesforce_token']}",
                                        "Content-Type": "application/json"},
                          json=payload, timeout=20)
        r.raise_for_status()
        return r.json().get("id"), f"Pushed to Salesforce {sobject}."
    if crm == "hubspot":
        if not creds["hubspot_token"]:
            return None, "HubSpot credentials not configured; payload prepared only."
        endpoint = {"contact": "contacts", "deal": "deals", "activity": "objects/calls"}[object_type]
        url = f"https://api.hubapi.com/crm/v3/objects/{endpoint}"
        r = requests.post(url, headers={"Authorization": f"Bearer {creds['hubspot_token']}",
                                        "Content-Type": "application/json"},
                          json={"properties": payload}, timeout=20)
        r.raise_for_status()
        return r.json().get("id"), f"Pushed to HubSpot {endpoint}."
    raise ValueError(f"Unsupported CRM: {crm}")


def sync_contact(lead: dict[str, Any], crm: str) -> dict[str, Any]:
    key = _normalise_crm(crm)
    payload = map_lead_to_crm(lead, key)
    try:
        remote_id, message = _push_live(key, "contact", payload)
        status = "success" if remote_id else "mapped"
        log_id = log_sync(key, "contact", lead.get("id"), "push", status, message, payload, remote_id)
        return {"entity": "contact", "status": status, "message": message,
                "remote_id": remote_id, "log_id": log_id, "payload": payload}
    except Exception as exc:
        log_id = log_sync(key, "contact", lead.get("id"), "push", "failed", str(exc), payload)
        return {"entity": "contact", "status": "failed", "message": str(exc), "log_id": log_id, "payload": payload}


def sync_deal(lead: dict[str, Any], crm: str) -> dict[str, Any]:
    key = _normalise_crm(crm)
    stage = map_deal_stage(lead.get("lead_status"), key)
    if key == "salesforce":
        payload = {
            "Name": f"{lead.get('company_name', 'Deal')} - SalesGenie",
            "StageName": stage,
            "Amount": float(lead.get("annual_revenue") or 0),
            "Description": lead.get("notes") or "",
        }
    else:
        payload = {
            "dealname": f"{lead.get('company_name', 'Deal')} - SalesGenie",
            "dealstage": stage,
            "amount": str(float(lead.get("annual_revenue") or 0)),
            "description": lead.get("notes") or "",
        }
    try:
        remote_id, message = _push_live(key, "deal", payload)
        status = "success" if remote_id else "mapped"
        log_id = log_sync(key, "deal", lead.get("id"), "push", status, message, payload, remote_id)
        return {"entity": "deal", "status": status, "stage": stage,
                "message": message, "remote_id": remote_id, "log_id": log_id, "payload": payload}
    except Exception as exc:
        log_id = log_sync(key, "deal", lead.get("id"), "push", "failed", str(exc), payload)
        return {"entity": "deal", "status": "failed", "stage": stage, "message": str(exc), "log_id": log_id, "payload": payload}


def sync_activity(activity: dict[str, Any], crm: str) -> dict[str, Any]:
    key = _normalise_crm(crm)
    mapped_type = map_activity_type(activity.get("activity_type", "note"), key)
    if key == "salesforce":
        payload = {"Subject": activity.get("subject") or mapped_type,
                   "Description": activity.get("body") or "", "Type": mapped_type}
    else:
        payload = {"hs_call_title": activity.get("subject") or mapped_type,
                   "hs_call_body": activity.get("body") or "", "hs_activity_type": mapped_type}
    try:
        remote_id, message = _push_live(key, "activity", payload)
        status = "success" if remote_id else "mapped"
        log_id = log_sync(key, "activity", activity.get("id"), "push", status, message, payload, remote_id)
        return {"entity": "activity", "status": status, "activity_type": mapped_type,
                "message": message, "remote_id": remote_id, "log_id": log_id, "payload": payload}
    except Exception as exc:
        log_id = log_sync(key, "activity", activity.get("id"), "push", "failed", str(exc), payload)
        return {"entity": "activity", "status": "failed", "activity_type": mapped_type,
                "message": str(exc), "log_id": log_id, "payload": payload}


def sync_lead(lead: dict[str, Any], crm: str, entities: list[str] | None = None) -> dict[str, Any]:
    key = _normalise_crm(crm)
    wanted = {e.lower() for e in (entities or ["contact", "deal", "activities"])}
    results: list[dict[str, Any]] = []
    if "contact" in wanted:
        results.append(sync_contact(lead, key))
    if "deal" in wanted:
        results.append(sync_deal(lead, key))
    if "activities" in wanted or "activity" in wanted:
        with connect() as conn:
            rows = conn.execute("SELECT * FROM activities WHERE lead_id = ? ORDER BY id",
                               (lead.get("id"),)).fetchall()
        for row in rows:
            results.append(sync_activity(dict(row), key))
    ok = all(r["status"] in ("success", "mapped") for r in results) if results else True
    return {"crm": key, "lead_id": lead.get("id"), "synced": len(results), "ok": ok, "results": results}
