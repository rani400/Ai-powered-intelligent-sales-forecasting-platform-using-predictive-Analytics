# SalesGenie AI � Complete Project Documentation

**Project Name:** SalesGenie AI  
**Version:** 1.0.0  
**Date:** October 2026  
**Technology Stack:** FastAPI, Streamlit, SQLite, Pydantic  
**Modules Implemented:** Lead Management, Lead Intelligence, AI Outreach, Lead Scoring, Conversation Intelligence

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Objectives](#objectives)
3. [System Architecture](#system-architecture)
4. [Module Details](#module-details)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Request/Response Examples](#requestresponse-examples)
8. [Scoring Algorithm Details](#scoring-algorithm-details)
9. [Project Structure](#project-structure)
10. [Installation & Setup](#installation--setup)
11. [Configuration](#configuration)
12. [Role & Responsibility Matrix](#role--responsibility-matrix)
13. [Testing Guidelines](#testing-guidelines)
14. [Future Enhancements](#future-enhancements)
15. [Notes & Constraints](#notes--constraints)
16. [Appendix](#appendix)

---

## Project Overview

SalesGenie AI is a lightweight CRM assistant implementing five modules:
1. **Lead Management** � CRUD operations for prospect records
2. **Lead Intelligence** � Company analysis and insights
3. **AI Outreach** � Personalized email draft generation
4. **Lead Scoring** � Rule-based qualification scoring
5. **Conversation Intelligence** � Summarize sales calls and extract action items automatically

This is a standalone reference implementation designed for learning and demonstration purposes.

---

## Module Workflows (Detailed)

### Module 1: Lead Management Workflow
1. **Create Lead**: User fills form in Streamlit → POST to `/leads` → Pydantic validates (`LeadCreate`) → SQL INSERT → Returns created lead with auto-generated ID → UI refreshes cache
2. **List/Search/Filter**: User enters search term or selects status → GET `/leads` with query params → SQL builds dynamic WHERE clauses (LIKE for search across 4 fields) → Returns ordered results (created_at DESC, id DESC) → Displayed in dataframe
3. **Update Lead**: User selects lead, edits status/engagement/notes → PATCH `/leads/{id}` with partial data → Validates via `LeadUpdate` (excludes unset) → SQL UPDATE with assignments → Sets `updated_at=CURRENT_TIMESTAMP` → Returns updated row
4. **Delete Lead**: User clicks delete → DELETE `/leads/{id}` → SQL DELETE → Returns confirmation message

### Module 2: Lead Intelligence Workflow
1. User selects a lead from dropdown
2. Clicks "Analyze company" → GET `/leads/{id}/intelligence`
3. Backend fetches lead via `get_lead()` → Calls `company_analysis(lead)` and `score_lead(lead)` in parallel
4. `company_analysis()` determines industry (lowercase match against hints), builds needs string, evaluates opportunities based on engagement/flags
5. `score_lead()` applies all rules, sums points (capped at 100), determines tier, selects recommendation
6. Returns combined result displayed in UI (summary, score, needs, opportunities)

### Module 3: AI Outreach Workflow
1. User selects lead, chooses tone and goal
2. Clicks generate → POST `/leads/{id}/outreach` with `{"tone": ..., "goal": ...}`
3. Backend fetches lead → Calls `generate_outreach(lead, tone, goal)`
4. If `GROQ_API_KEY` exists: Builds prompt with lead details → POST to Groq API with model `openai/gpt-oss-20b` → Parses response → Returns with note "Generated via Groq. Draft only."
5. If API fails or no key: Uses template based on tone (professional/friendly/concise) → Returns with note about draft only, no sending
6. UI displays subject and body

### Module 5: Conversation Intelligence Workflow
1. User selects a lead (optional), chooses meeting type, and pastes a sales call transcript
2. Clicks "Summarize Call & Extract Action Items" → POST `/conversations/summarize` with `{"lead_id": ..., "meeting_type": ..., "transcript": "..."}`
3. Backend calls `summarize_conversation(transcript, meeting_type)`
4. If `GROQ_API_KEY` exists: Sends prompt to Groq API with model `openai/gpt-oss-20b` → Parses JSON response with summary, key_points, customer_concerns, action_items, next_steps
5. If API fails or no key: Uses rule-based keyword extraction (detects action keywords like "follow up", "schedule", "send", "demo", "proposal", etc.) → Returns with note about rule-based extraction
6. Optionally saves the conversation record to the `conversations` table in SQLite
7. UI displays summary, key discussion points, customer concerns, action items (with assignee/due date), and next steps

### Module 5: Conversation Intelligence Workflow
1. User uploads/pastes sales call transcript or conversation notes in the Conversation Intelligence tab
2. Clicks "Summarize Call & Extract Action Items" ? POST `/conversations/summarize` with `{"transcript": "...", "meeting_type": "..."}`
3. Backend processes transcript using NLP/LLM logic ? Generates call summary, key discussion points, customer concerns, action items with assignees/due dates, next steps
4. If `GROQ_API_KEY` exists: Uses LLM for intelligent summarization and action item extraction ? Returns structured results
5. If API fails or no key: Uses rule-based extraction (keywords: action, follow up, schedule, send, review, call back) ? Returns with note about extraction method
6. UI displays summary, key points, action items table, and next steps

---

## Request/Response Examples

### Create Lead
**Request:**
```json
POST /leads
{
  "company_name": "Acme Corp",
  "industry": "Technology",
  "contact_name": "John Doe",
  "contact_title": "CTO",
  "email": "john@acme.com",
  "phone": "+1234567890",
  "company_size": 150,
  "engagement_score": 75,
  "website_visits": 5,
  "email_opens": 3,
  "email_clicks": 2,
  "budget_confirmed": true,
  "need_identified": true,
  "decision_maker": true,
  "lead_status": "Qualified",
  "notes": "Interested in automation"
}
```

**Response (201):**
```json
{
  "id": 1,
  "company_name": "Acme Corp",
  "industry": "Technology",
  "contact_name": "John Doe",
  "contact_title": "CTO",
  "email": "john@acme.com",
  "phone": "+1234567890",
  "company_size": 150,
  "annual_revenue": 0,
  "engagement_score": 75,
  "website_visits": 5,
  "email_opens": 3,
  "email_clicks": 2,
  "budget_confirmed": true,
  "need_identified": true,
  "decision_maker": true,
  "lead_status": "Qualified",
  "notes": "Interested in automation",
  "created_at": "2026-10-27 08:36:08",
  "updated_at": "2026-10-27 08:36:08"
}
```

### Lead Intelligence
**Response:**
```json
{
  "lead_id": 1,
  "company_analysis": {
    "company_name": "Acme Corp",
    "industry": "Technology",
    "company_summary": "Acme Corp is recorded as an organisation in the Technology industry.",
    "potential_needs": "automation, scalability, integration, and security",
    "opportunities": [
      "Engagement is promising; follow up with a specific use case.",
      "Discuss scope, decision criteria, and implementation timeline.",
      "Connect product value directly to the stated business need."
    ],
    "source_note": "Insights are inferred from user-supplied lead fields; company facts have not been independently verified."
  },
  "lead_scoring": {
    "lead_score": 95,
    "qualification_tier": "High",
    "conversion_probability": 78,
    "probability_components": {
      "engagement": 25,
      "fit": 20,
      "intent": 18,
      "decision_readiness": 15
    },
    "probability_note": "Conversion probability calculated using engagement, fit, intent, and decision readiness factors; stored in lead_scores table.",
    "scoring_method": "Explainable rule-based baseline; not a trained machine-learning model.",
    "factors": [
      {"factor": "High engagement", "points": 25},
      {"factor": "Industry fit", "points": 20},
      {"factor": "Strong intent signals", "points": 18},
      {"factor": "Decision readiness", "points": 15}
    ],
    "recommendation": "Prioritise a personalised follow-up and propose a discovery call."
  }
}
```

### Outreach Draft
**Request:**
```json
POST /leads/1/outreach
{
  "tone": "professional",
  "goal": "schedule a 15-minute discovery call"
}
```

**Response (Template):**
```json
{
  "subject": "Exploring priorities at Acme Corp",
  "body": "Hi John,\n\nI am reaching out to learn more about the current priorities at Acme Corp. For organisations in Technology, improving process efficiency and achieving measurable outcomes can be important. I would be glad to understand your priorities and explore whether we may be able to help.\n\nWould you be available to schedule a 15-minute discovery call?\n\nBest regards,\nSales Team",
  "note": "Draft only. Verify details and personalise before sending; this endpoint does not send email."
}
```

---

## Scoring Algorithm Details

### Rule Weights
| Condition | Points | Factor Label |
|-----------|--------|--------------|
| Engagement score >= 70 | 25 | High engagement |
| Email clicks > 0 | 10 | Clicked an outreach email |
| Email opens >= 2 | 5 | Opened emails more than once |
| Website visits >= 3 | 10 | Repeated website visits |
| Budget confirmed (true) | 15 | Budget confirmed |
| Business need identified (true) | 15 | Business need identified |
| Decision-maker identified (true) | 10 | Decision-maker identified |
| Company size >= 100 | 5 | Company size may support a larger engagement |
| Industry not Unknown/empty/other | 5 | Industry information available |

**Total possible:** 100 | **Capped at:** 100

### Tier Classification
- **High:** score >= 70
- **Medium:** score >= 40 and < 70
- **Low:** score < 40

### Recommendations
- **High:** "Prioritise a personalised follow-up and propose a discovery call."
- **Medium:** "Share a relevant case study and ask one qualifying question."
- **Low:** "Gather missing information and use a low-pressure nurture message."

---

## Role & Responsibility Matrix

| Role | Component | Responsibilities |
|------|-----------|-----------------|
| **Backend Developer** | app/main.py, app/database.py | API design, routing, database schema, CRUD operations, startup events |
| **Data/Validation Engineer** | app/schemas.py | Pydantic models, request validation, type safety, constraints |
| **Business Logic Engineer** | app/services.py | Scoring rules, intelligence logic, outreach generation, industry hints, external API integration (Groq) |
| **Frontend Developer** | frontend.py | Streamlit UI, form handling, data display, API integration, caching, user experience |
| **DevOps/Setup** | run_*.bat, requirements.txt | Environment setup, dependency management, deployment scripts |
| **Data Manager** | data/ | Database storage, sample data, data persistence |

---

## Dependencies Details

| Package | Purpose | Notes |
|---------|---------|-------|
| fastapi | Web framework | Modern async framework, auto-docs at /docs |
| uvicorn[standard] | ASGI server | Includes watchfiles for --reload |
| pydantic | Validation | v2 with EmailStr, Field constraints |
| streamlit | UI framework | Reactive UI, caching, forms |
| requests | HTTP client | Frontend-backend communication, Groq API calls |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Backend API is not running yet" | Backend not started | Start with `uvicorn app.main:app --reload` on port 8000 |
| Port 8000 in use | Previous process | Kill with `taskkill /PID <pid> /F` |
| ModuleNotFoundError | Missing deps | `pip install -r requirements.txt` |
| Database errors | Corrupted DB | Delete `data/salesgenie.db` and restart (recreates schema) |
| Groq API fails | No key/rate limit | Auto-falls back to template |
| Streamlit warnings | Deprecated API | Use `width='stretch'` not `use_container_width` |

---

## Quick Reference Commands

```powershell
# Start backend
.\.venv312\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Start frontend
.\.venv312\Scripts\python.exe -m streamlit run frontend.py

# Check health
Invoke-RestMethod -Uri http://127.0.0.1:8000/health

# API docs
Start-Process "http://127.0.0.1:8000/docs"
```

**Document Version:** 1.1 | **Last Updated:** 2026-10-27

---

## CRM Integration & Sync (Salesforce / HubSpot)

### Field Mapping Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/crm/field-mappings` | Show mapping for both CRMs (or `?crm=salesforce\|hubspot`) |
| GET | `/crm/field-mappings/validate?crm=...` | Validate completeness and duplicates |
| POST | `/crm/leads/{id}/export` | Convert lead to CRM-ready payload |
| POST | `/crm/leads/import` | Map a CRM record back to lead fields |

### Sync Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/crm/deal-stages` | Deal-stage mapping per CRM |
| POST | `/crm/activities/{lead_id}` | Record a local activity (call/email/meeting/note) |
| GET | `/crm/activities/{lead_id}` | List activities for a lead |
| POST | `/crm/sync/leads/{lead_id}` | Sync contact, deal, and activities (`{crm, entities}`) |
| GET | `/crm/sync/logs` | Query CRM_Sync_Logs (filters: crm, entity_type, status) |

### Deal Stage Mapping
| Lead Status | Salesforce Stage | HubSpot Stage |
|-------------|------------------|---------------|
| New | Prospecting | appointmentscheduled |
| Contacted | Prospecting | qualifiedtobuy |
| Qualified | Qualification | presentationscheduled |
| Proposal | Proposal/Price Quote | decisionmakerboughtin |
| Negotiation | Negotiation/Review | contractsent |
| Won | Closed Won | closedwon |
| Lost | Closed Lost | closedlost |

### CRM_Sync_Logs Table
Columns: `id, crm, entity_type (contact/activity/deal), entity_id, direction, status (success/mapped/failed), message, payload, remote_id, created_at`.

### Live Push Configuration (optional)
Set these env vars to enable real API pushes; otherwise sync prepares and logs payloads as `mapped` (dry run):
- `SALESFORCE_INSTANCE_URL`, `SALESFORCE_ACCESS_TOKEN`
- `HUBSPOT_ACCESS_TOKEN`

**Document Version:** 1.2 | **Last Updated:** 2026-11-19
