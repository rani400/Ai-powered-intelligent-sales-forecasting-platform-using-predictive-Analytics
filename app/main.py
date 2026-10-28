from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from .database import connect, init_db, row_to_dict
from .schemas import LeadCreate, LeadUpdate, OutreachRequest
from .services import company_analysis, score_lead, generate_outreach
import csv
import io

app = FastAPI(title="SalesGenie AI — Modules 1–4", version="1.0.0",
              description="Lead Management, Lead Intelligence, AI Outreach, and Lead Scoring only.")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "modules": ["lead-management", "lead-intelligence", "ai-outreach", "lead-scoring"]}

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
    return score_lead(get_lead(lead_id))

@app.post("/leads/{lead_id}/outreach")
def outreach(lead_id: int, payload: OutreachRequest):
    lead = get_lead(lead_id)
    return generate_outreach(lead, payload.tone, payload.goal)
