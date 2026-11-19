from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from .database import connect, init_db, row_to_dict
from .schemas import LeadCreate, LeadUpdate, OutreachRequest, ConversationSummarizeRequest
from .services import company_analysis, score_lead, generate_outreach, next_best_action, summarize_conversation
import json
import csv
import io


app = FastAPI(title="SalesGenie AI — Modules 1–5", version="1.0.0",
              description="Lead Management, Lead Intelligence, AI Outreach, Lead Scoring, and Conversation Intelligence.")

@app.get("/leads/{lead_id}/next-best-action")
def get_next_best_action(lead_id: int):
    lead = get_lead(lead_id)
    score_data = score_lead(lead)
    return next_best_action(lead, score_data)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "modules": ["lead-management", "lead-intelligence", "ai-outreach", "lead-scoring", "conversation-intelligence"]}

# Module 1 — Lead Management CRUD
@app.post("/leads", status_code=201)
def create_lead(payload: LeadCreate):
    data = payload.model_dump()
    columns = list(data.keys())
    values = [int(v) if isinstance(v, bool) else v for v in data.values()]
    placeholders = ",".join("?" for _ in columns)
    with connect() as conn:
        cur = conn.execute(f"INSERT INTO leads ({','.join(columns)}) VALUES ({placeholders})", values)
        row = conn.execute("SELECT * FROM leads WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)

@app.get("/leads")
def list_leads(search: str | None = Query(default=None), status: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=500)):
    sql, params = "SELECT * FROM leads WHERE 1=1", []
    if search:
        sql += " AND (company_name LIKE ? OR contact_name LIKE ? OR email LIKE ? OR industry LIKE ?)"
        term = f"%{search}%"; params.extend([term, term, term, term])
    if status:
        sql += " AND lead_status = ?"; params.append(status)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"; params.append(limit)
    with connect() as conn:
        return [row_to_dict(r) for r in conn.execute(sql, params).fetchall()]

@app.get("/leads/{lead_id}")
def get_lead(lead_id: int):
    with connect() as conn: row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    if not row: raise HTTPException(404, "Lead not found")
    return row_to_dict(row)

@app.patch("/leads/{lead_id}")
def update_lead(lead_id: int, payload: LeadUpdate):
    changes = payload.model_dump(exclude_unset=True)
    if not changes: raise HTTPException(400, "Provide at least one field to update")
    if "id" in changes: changes.pop("id")
    assignments = ",".join(f"{k}=?" for k in changes)
    values = [int(v) if isinstance(v, bool) else v for v in changes.values()]
    with connect() as conn:
        cur = conn.execute(f"UPDATE leads SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values + [lead_id])
        if cur.rowcount == 0: raise HTTPException(404, "Lead not found")
        return row_to_dict(conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone())

@app.delete("/leads/{lead_id}")
def delete_lead(lead_id: int):
    with connect() as conn:
        cur = conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
        if cur.rowcount == 0: raise HTTPException(404, "Lead not found")
    return {"message": "Lead deleted", "lead_id": lead_id}


@app.post("/leads/import")
async def import_leads(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files are allowed")
    
    content = await file.read()
    text = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(text))
    
    inserted = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):
        try:
            data = {}
            if row.get('company_name'):
                data['company_name'] = row['company_name'].strip()
            else:
                errors.append(f"Row {row_num}: company_name is required")
                continue
            if row.get('industry'):
                data['industry'] = row['industry'].strip()
            else:
                data['industry'] = 'Unknown'
            if row.get('contact_name'):
                data['contact_name'] = row['contact_name'].strip()
            else:
                data['contact_name'] = 'there'
            if row.get('contact_title'):
                data['contact_title'] = row['contact_title'].strip()
            else:
                data['contact_title'] = ''
            if row.get('email') and row['email'].strip():
                data['email'] = row['email'].strip()
            else:
                data['email'] = None
            if row.get('phone') and row['phone'].strip():
                data['phone'] = row['phone'].strip()
            else:
                data['phone'] = None
            if row.get('company_size'):
                try:
                    data['company_size'] = int(float(row['company_size']))
                except:
                    data['company_size'] = 0
            else:
                data['company_size'] = 0
            if row.get('engagement_score'):
                try:
                    data['engagement_score'] = float(row['engagement_score'])
                except:
                    data['engagement_score'] = 0
            else:
                data['engagement_score'] = 0
            if row.get('website_visits'):
                try:
                    data['website_visits'] = int(float(row['website_visits']))
                except:
                    data['website_visits'] = 0
            else:
                data['website_visits'] = 0
            if row.get('email_opens'):
                try:
                    data['email_opens'] = int(float(row['email_opens']))
                except:
                    data['email_opens'] = 0
            else:
                data['email_opens'] = 0
            if row.get('email_clicks'):
                try:
                    data['email_clicks'] = int(float(row['email_clicks']))
                except:
                    data['email_clicks'] = 0
            else:
                data['email_clicks'] = 0
            if row.get('budget_confirmed'):
                data['budget_confirmed'] = row['budget_confirmed'].strip().lower() in ['true', '1', 'yes']
            else:
                data['budget_confirmed'] = False
            if row.get('need_identified'):
                data['need_identified'] = row['need_identified'].strip().lower() in ['true', '1', 'yes']
            else:
                data['need_identified'] = False
            if row.get('decision_maker'):
                data['decision_maker'] = row['decision_maker'].strip().lower() in ['true', '1', 'yes']
            else:
                data['decision_maker'] = False
            if row.get('lead_status'):
                data['lead_status'] = row['lead_status'].strip()
            else:
                data['lead_status'] = 'New'
            if row.get('notes'):
                data['notes'] = row['notes'].strip()
            else:
                data['notes'] = ''
            
            columns = list(data.keys())
            values = [int(v) if isinstance(v, bool) else v for v in data.values()]
            placeholders = ",".join("?" for _ in columns)
            with connect() as conn:
                conn.execute(f"INSERT INTO leads ({','.join(columns)}) VALUES ({placeholders})", values)
                conn.commit()
            inserted += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    return {"inserted": inserted, "errors": errors, "total_rows": inserted + len(errors)}

# Modules 2–4 — AI/ML endpoints
@app.get("/leads/{lead_id}/intelligence")
def lead_intelligence(lead_id: int):
    lead = get_lead(lead_id)
    return {"lead_id": lead_id, "company_analysis": company_analysis(lead), "lead_scoring": score_lead(lead)}

@app.get("/leads/{lead_id}/company-analysis")
def company_profile_analysis(lead_id: int):
    return company_analysis(get_lead(lead_id))

@app.get("/leads/{lead_id}/score")
def lead_score(lead_id: int):
    lead = get_lead(lead_id)
    result = score_lead(lead)
    # Store in lead_scores table
    try:
        import json
        from .database import connect
        factors_json = json.dumps(result.get("factors", []))
        pc = result.get("probability_components", {})
        with connect() as conn:
            conn.execute('''INSERT INTO lead_scores 
                (lead_id, lead_score, conversion_probability, engagement_score, fit_score, intent_score, decision_readiness, factors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (lead_id, result['lead_score'], result.get('conversion_probability', 0),
                 pc.get('engagement', 0), pc.get('fit', 0), pc.get('intent', 0), pc.get('decision_readiness', 0),
                 factors_json))
            conn.commit()
    except Exception:
        pass
    return result

@app.get("/leads/{lead_id}/next-best-action")
def get_next_best_action(lead_id: int):
    lead = get_lead(lead_id)
    score_data = score_lead(lead)
    return next_best_action(lead, score_data)

@app.post('/leads/{lead_id}/outreach')
def outreach(lead_id: int, payload: OutreachRequest):
    lead = get_lead(lead_id)
    return generate_outreach(lead, payload.tone, payload.goal)

# Module 5 — Conversation Intelligence
@app.post("/conversations/summarize")
def summarize_call(payload: ConversationSummarizeRequest):
    result = summarize_conversation(payload.transcript, payload.meeting_type)
    if payload.lead_id:
        try:
            from .database import save_conversation
            save_conversation(payload.lead_id, payload.meeting_type, payload.transcript, result.get("summary",""), json.dumps(result.get("key_points",[])), json.dumps(result.get("customer_concerns",[])), json.dumps(result.get("action_items",[])), json.dumps(result.get("next_steps",[])))
        except Exception:
            pass
    return result

# ===== CRM Integration (Salesforce / HubSpot field mapping) =====
from .crm import get_field_mappings, map_lead_to_crm, map_crm_to_lead, validate_field_mappings
from .schemas import CrmImportRequest, CrmExportRequest

@app.get("/crm/field-mappings")
def crm_field_mappings(crm: str | None = Query(default=None)):
    try:
        return get_field_mappings(crm)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.get("/crm/field-mappings/validate")
def crm_field_mappings_validate(crm: str = Query(...)):
    try:
        return validate_field_mappings(crm)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.post("/crm/leads/{lead_id}/export")
def crm_export_lead(lead_id: int, payload: CrmExportRequest):
    lead = get_lead(lead_id)
    try:
        mapped = map_lead_to_crm(lead, payload.crm)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if not payload.include_empty:
        mapped = {k: v for k, v in mapped.items() if v not in (None, "")}
    return {"crm": payload.crm, "lead_id": lead_id, "field_count": len(mapped), "payload": mapped}

@app.post("/crm/leads/import")
def crm_import_lead(payload: CrmImportRequest):
    try:
        mapped = map_crm_to_lead(payload.data, payload.crm)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if not payload.create_lead:
        return {"crm": payload.crm, "mapped": mapped}
    if not mapped.get("company_name"):
        raise HTTPException(400, "Mapped data is missing company_name; cannot create lead")
    from .schemas import LeadCreate
    create = LeadCreate(**{k: v for k, v in mapped.items() if k in LeadCreate.model_fields})
    return create_lead(create)

# ===== CRM Sync (contacts, activities, deal stages) + CRM_Sync_Logs =====
from .crm_sync import (get_deal_stages, sync_lead, get_sync_logs, log_sync)
from .schemas import CrmSyncRequest, ActivityCreate

@app.get("/crm/deal-stages")
def crm_deal_stages(crm: str | None = Query(default=None)):
    try:
        return get_deal_stages(crm)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.post("/crm/activities/{lead_id}", status_code=201)
def crm_create_activity(lead_id: int, payload: ActivityCreate):
    get_lead(lead_id)
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO activities (lead_id, activity_type, subject, body) VALUES (?, ?, ?, ?)",
            (lead_id, payload.activity_type, payload.subject, payload.body))
        conn.commit()
        row = conn.execute("SELECT * FROM activities WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)

@app.get("/crm/activities/{lead_id}")
def crm_list_activities(lead_id: int):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM activities WHERE lead_id=? ORDER BY id DESC", (lead_id,)).fetchall()
    return [dict(r) for r in rows]

@app.post("/crm/sync/leads/{lead_id}")
def crm_sync_lead(lead_id: int, payload: CrmSyncRequest):
    lead = get_lead(lead_id)
    try:
        return sync_lead(lead, payload.crm, payload.entities)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.get("/crm/sync/logs")
def crm_sync_logs(crm: str | None = Query(default=None),
                  entity_type: str | None = Query(default=None),
                  status: str | None = Query(default=None),
                  limit: int = Query(default=100, ge=1, le=500)):
    return get_sync_logs(crm, entity_type, status, limit)
