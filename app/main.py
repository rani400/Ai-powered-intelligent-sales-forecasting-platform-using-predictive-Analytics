from fastapi import FastAPI, HTTPException, Query
from .database import connect, init_db, row_to_dict
from .schemas import LeadCreate, LeadUpdate, OutreachRequest
from .services import company_analysis, score_lead, generate_outreach

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
