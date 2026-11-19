# SalesGenie AI — Module 5 & CRM Integration Documentation

**Scope:** Conversation Intelligence (meeting/call summarization + Sales_Interactions) and CRM Integration & Sync (Salesforce / HubSpot field mapping, contacts, activities, deal stages, sync logs).

**Stack:** FastAPI · Pydantic · SQLite · Streamlit · Groq (LLM)

**Env var for AI summarization:** `GROQ_API_KEY` (model `openai/gpt-oss-20b`). If unset or the API fails, the app falls back to rule-based extraction.

---

# Part A — Module 5: Conversation Intelligence

## A1. Purpose
Automatically summarize sales calls/meetings, extract key discussion points and action items, and store each interaction in the `Sales_Interactions` table for later review.

## A2. Files
| File | Responsibility |
|------|----------------|
| `app/services.py` | `summarize_conversation(transcript, meeting_type)` — Groq LLM path + rule-based fallback |
| `app/schemas.py` | `InteractionSummarizeRequest`, `ConversationSummarizeRequest` |
| `app/database.py` | `sales_interactions` + `conversations` tables; `save_interaction`, `list_interactions`, `get_interaction`, `delete_interaction`, `save_conversation` |
| `app/main.py` | `/interactions/*` and `/conversations/summarize` endpoints |
| `frontend.py` | "Conversation Intelligence" page |

## A3. Summarization output
`summarize_conversation` returns:
- `summary` — short narrative of the call
- `key_points` — key discussion points (stored as `key_discussion_points`)
- `customer_concerns` — objections/risks raised
- `action_items` — list of `{task, assignee, due_date}`
- `next_steps` — follow-up actions
- `note` — which engine produced it (`Generated via Groq.` or `Rule-based extraction...`)

### Groq path
Sends the transcript to `https://api.groq.com/openai/v1/chat/completions` with a JSON-output prompt. Code strips ```json fences and re-extracts the JSON object before parsing.

### Rule-based fallback
- Splits transcript into sentences.
- Key points: sentences containing cues like need, budget, timeline, competitor, integration, concern.
- Action items: sentences with action cues (will, send, schedule, demo, proposal, review, follow up), assignee heuristics (Rep vs Prospect), due dates (today/tomorrow/Friday/next week).
- Concerns/next steps from keyword signals.

## A4. Sales_Interactions table
```sql
CREATE TABLE sales_interactions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 lead_id INTEGER,
 interaction_type TEXT NOT NULL DEFAULT 'call',   -- call|meeting|demo|follow-up|other
 title TEXT NOT NULL DEFAULT '',
 participants TEXT NOT NULL DEFAULT '',
 transcript TEXT NOT NULL,
 summary TEXT NOT NULL DEFAULT '',
 key_discussion_points TEXT NOT NULL DEFAULT '[]',
 action_items TEXT NOT NULL DEFAULT '[]',
 customer_concerns TEXT NOT NULL DEFAULT '[]',
 next_steps TEXT NOT NULL DEFAULT '[]',
 sentiment TEXT NOT NULL DEFAULT '',
 source TEXT NOT NULL DEFAULT 'rule-based',       -- groq|rule-based
 occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## A5. Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/interactions/summarize` | Summarize a meeting/call and store in Sales_Interactions (201) |
| GET | `/interactions` | List stored interactions (`?lead_id=&interaction_type=&limit=`) |
| GET | `/interactions/{id}` | Fetch one interaction |
| DELETE | `/interactions/{id}` | Delete an interaction |
| POST | `/conversations/summarize` | Summarize and optionally save to `conversations` (legacy module-5 endpoint) |

### Example — summarize & store
```http
POST /interactions/summarize
{
  "lead_id": 1,
  "interaction_type": "call",
  "title": "Discovery call",
  "participants": "John Doe, Sales Rep",
  "transcript": "Rep: What are your priorities? Prospect: We need CRM integration and budget is limited. Rep: I will send a proposal by Friday and schedule a demo next week."
}
```

Response (201):
```json
{
  "id": 1,
  "lead_id": 1,
  "interaction_type": "call",
  "title": "Discovery call",
  "summary": "The prospect needs CRM integration with budget constraints...",
  "key_discussion_points": ["CRM integration is a top priority", "Budget constraints"],
  "action_items": [
    {"task": "Send proposal", "assignee": "Rep", "due_date": "2026-11-24"},
    {"task": "Schedule demo", "assignee": "Rep", "due_date": "2026-11-26"}
  ],
  "customer_concerns": ["Limited budget"],
  "next_steps": ["Send proposal", "Schedule product demo"],
  "source": "groq",
  "created_at": "2026-11-19 12:04:00"
}
```

## A6. Conversations table (legacy `/conversations/summarize`)
Stores transcript, summary, key_points, customer_concerns, action_items, next_steps. Used by the earlier Conversation Intelligence page.

---

# Part B — CRM Integration & Sync (Salesforce / HubSpot)

## B1. Purpose
Map local leads to CRM fields, prepare CRM-ready payloads, sync contacts/activities/deals, and log every attempt in `crm_sync_logs`.

## B2. Files
| File | Responsibility |
|------|----------------|
| `app/crm.py` | Field maps + `map_lead_to_crm`, `map_crm_to_lead`, `get_field_mappings`, `validate_field_mappings` |
| `app/crm_sync.py` | Deal-stage maps, activity-type maps, `sync_contact`, `sync_deal`, `sync_activity`, `sync_lead`, `log_sync`, `get_sync_logs` |
| `app/database.py` | `activities`, `crm_sync_logs` tables; interaction helpers |
| `app/main.py` | `/crm/*` endpoints |
| `app/schemas.py` | `CrmImportRequest`, `CrmExportRequest`, `CrmSyncRequest`, `ActivityCreate` |

## B3. Field mapping
### Salesforce
| Lead field | Salesforce field |
|-----------|------------------|
| company_name | Company |
| industry | Industry |
| contact_name | LastName |
| contact_title | Title |
| email | Email |
| phone | Phone |
| company_size | NumberOfEmployees |
| annual_revenue | AnnualRevenue |
| engagement_score | Engagement_Score__c |
| website_visits | Website_Visits__c |
| email_opens | Email_Opens__c |
| email_clicks | Email_Clicks__c |
| budget_confirmed | Budget_Confirmed__c |
| need_identified | Need_Identified__c |
| decision_maker | Decision_Maker__c |
| lead_status | Status |
| notes | Description |

### HubSpot
| Lead field | HubSpot property |
|-----------|------------------|
| company_name | company |
| industry | industry |
| contact_name | firstname / lastname (split) |
| contact_title | jobtitle |
| email | email |
| phone | phone |
| company_size | numberofemployees |
| annual_revenue | annualrevenue |
| engagement_score | engagement_score |
| website_visits | website_visits |
| email_opens | email_opens |
| email_clicks | email_clicks |
| budget_confirmed | budget_confirmed |
| need_identified | need_identified |
| decision_maker | decision_maker |
| lead_status | hs_lead_status |
| notes | hs_content_membership_notes |

## B4. Deal stage mapping
| Lead status | Salesforce StageName | HubSpot dealstage |
|-------------|----------------------|-------------------|
| New | Prospecting | appointmentscheduled |
| Contacted | Prospecting | qualifiedtobuy |
| Qualified | Qualification | presentationscheduled |
| Proposal | Proposal/Price Quote | decisionmakerboughtin |
| Negotiation | Negotiation/Review | contractsent |
| Won | Closed Won | closedwon |
| Lost | Closed Lost | closedlost |

## B5. Activity type mapping
| Local | Salesforce Type | HubSpot |
|-------|-----------------|---------|
| call | Call | CALL |
| email | Email | EMAIL |
| meeting | Meeting | MEETING |
| note | Note | NOTE |

## B6. Tables
```sql
CREATE TABLE activities (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 lead_id INTEGER NOT NULL,
 activity_type TEXT NOT NULL DEFAULT 'note',
 subject TEXT NOT NULL DEFAULT '',
 body TEXT NOT NULL DEFAULT '',
 occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE crm_sync_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 crm TEXT NOT NULL,
 entity_type TEXT NOT NULL,          -- contact|activity|deal
 entity_id INTEGER,
 direction TEXT NOT NULL DEFAULT 'push',
 status TEXT NOT NULL DEFAULT 'pending',  -- success|mapped|failed
 message TEXT NOT NULL DEFAULT '',
 payload TEXT,
 remote_id TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## B7. Endpoints
### Field mapping
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/crm/field-mappings` | Both CRM maps (`?crm=salesforce\|hubspot` for one) |
| GET | `/crm/field-mappings/validate?crm=...` | Validate completeness/duplicates |
| POST | `/crm/leads/{lead_id}/export` | Convert lead to CRM-ready payload |
| POST | `/crm/leads/import` | Map CRM record back to lead fields (optional `create_lead`) |

### Sync
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/crm/deal-stages` | Deal stage maps per CRM |
| POST | `/crm/activities/{lead_id}` | Record local activity (201) |
| GET | `/crm/activities/{lead_id}` | List lead activities |
| POST | `/crm/sync/leads/{lead_id}` | Sync contact + deal + activities |
| GET | `/crm/sync/logs` | Query CRM_Sync_Logs (`crm`, `entity_type`, `status`, `limit`) |

### Example — sync a lead
```http
POST /crm/sync/leads/1
{ "crm": "salesforce", "entities": ["contact", "deal", "activities"] }
```
Response:
```json
{
  "crm": "salesforce",
  "lead_id": 1,
  "synced": 3,
  "ok": true,
  "results": [
    {"entity": "contact", "status": "mapped", "message": "Salesforce credentials not configured; payload prepared only.", "log_id": 1},
    {"entity": "deal", "status": "mapped", "stage": "Qualification", "log_id": 2},
    {"entity": "activity", "status": "mapped", "activity_type": "Call", "log_id": 3}
  ]
}
```

## B8. Sync status values
- `success` — push succeeded and `remote_id` returned
- `mapped` — dry run: payload prepared, no credentials configured
- `failed` — push error (message captured)

## B9. Live push configuration (optional)
Set these env vars to push to a real CRM; otherwise the sync runs in dry-run mode and logs `mapped`:
- Salesforce: `SALESFORCE_INSTANCE_URL`, `SALESFORCE_ACCESS_TOKEN`
- HubSpot: `HUBSPOT_ACCESS_TOKEN`

Endpoints used when configured:
- Salesforce: `POST {INSTANCE_URL}/services/data/v60.0/sobjects/{Lead|Opportunity|Task}/`
- HubSpot: `POST https://api.hubapi.com/crm/v3/objects/{contacts|deals|objects/calls}`

---

# Part C — Running

```powershell
# Set Groq key for summarization (recommended)
$env:GROQ_API_KEY="<your-groq-key>"

# Backend
.\.venv312\Scripts\python.exe -m uvicorn app.main:app --reload

# Frontend (second terminal)
.\.venv312\Scripts\python.exe -m streamlit run frontend.py
```

- API documentation: `http://127.0.0.1:8000/docs`
- Health (lists all modules): `GET /health`

## Notes & limitations
- Summarization quality depends on transcript quality; Groq output is normalized to JSON before use.
- CRM mapping is transformation + orchestration. Live pushes require credentials and are not tested without them.
- No secrets are stored in code; all credentials come from environment variables.
- `Sales_Interactions` stores derived summaries, not audio; no transcription of audio is performed.
