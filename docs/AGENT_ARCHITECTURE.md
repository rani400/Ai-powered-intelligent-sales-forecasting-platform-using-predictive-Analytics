# Agent / Pipeline Architecture — SalesGenie AI

## 1. The flow being designed

```
Prospect data → Company analysis → Lead intelligence → Qualification score → Recommendations
```

This is the same pipeline that the project PDF describes as the agent workflow. In the current
implementation it is a **deterministic pipeline of typed services**, not an LLM-driven agent
graph. The reason is deliberate: every step is auditable, reproducible and testable, and the
outputs are stored so they can be compared over time.

The pipeline is structured so that each stage can later be replaced by a LangGraph node without
changing the surrounding interfaces.

---

## 2. Stage-by-stage mapping

| Stage | Input | Component | Output | Stored in |
| --- | --- | --- | --- | --- |
| 1. Prospect data | CSV upload or manual entry | `schemas/lead_schema.py` → `services/lead_import.py` | Validated `Lead` row | `leads` |
| 2. Company analysis | `Lead` row | `services/lead_intelligence.py` → `build_company_profile()` | Field-grounded company profile | in-memory |
| 3. Lead intelligence | Profile + sector reference | `services/lead_intelligence.py` | Business needs, opportunities, key insights, gaps | `company_insights` |
| 4. Qualification score | `Lead` row | `services/lead_intelligence.py` | 0–100 score + factor breakdown | `lead_scores` |
| 5. Recommendations | Insights + score | `services/outreach_generator.py` | Outreach draft (subject + body) | `outreach_campaigns` |

---

## 3. Request flow

```
Streamlit page
     │  HTTP (frontend/api_client.py)
     ▼
FastAPI route (routers/leads.py, routers/outreach.py)
     │  thin: parse + validate, no business rules
     ▼
Service layer (services/*.py)
     │  business rules, domain errors
     ▼
ORM (models/*.py) → SQLAlchemy → PostgreSQL / SQLite
```

Errors travel back the same path: a service raises a `DomainError` subclass, and a single
exception handler in `app/errors.py` converts it into the standard error envelope with the
correct HTTP status code.

---

## 4. Lead intelligence detail

```
                    ┌───────────────────────────────┐
                    │        Lead row               │
                    │  industry, company_size,      │
                    │  contact, email, phone,       │
                    │  status, notes                │
                    └───────────────┬───────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ Company profile  │  │ Sector reference │  │ Scoring factors  │
   │ (stored fields   │  │ (needs, opps,    │  │ (industry, size, │
   │  only)           │  │  triggers)       │  │  completeness,   │
   └────────┬─────────┘  └────────┬─────────┘  │  stage, channel) │
            │                     │             └────────┬─────────┘
            └──────────┬──────────┘                        │
                       ▼                                    ▼
            ┌────────────────────────┐          ┌────────────────────┐
            │  LeadInsightResponse   │          │  QualificationScore│
            │  profile, needs,       │◄─────────┤  0-100 + factors   │
            │  opportunities,        │          └────────────────────┘
            │  insights, gaps        │
            └───────────┬────────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │  company_insights row  │
            │  + lead_scores row     │
            └────────────────────────┘
```

**Grounding rule.** Sector reference data describes *sectors*, never the specific company. The
service phrases every need and opportunity as a hypothesis for the salesperson to validate, and
reports missing fields as gaps instead of filling them in. This is enforced by test
`TC-44` (no invented revenue, headcount, funding or employee claims).

---

## 5. Outreach generation detail

```
Lead row + request options
        │
        ▼
services/outreach_generator.py → PromptTemplate
   • tone         → professional | friendly
   • email_length → short | detailed
   • goal         → product_introduction | meeting | follow_up
   • industry     → sector guidance (framed as sector context, not company facts)
        │
        ▼
services/outreach_generator.py
   ├── LLM_API_KEY set?  ── yes ─► POST {LLM_BASE_URL}/chat/completions
   │                                    │  timeout / error → UpstreamError (HTTP 502)
   │                                    ▼
   │                              parse SUBJECT: / BODY:
   └── no ──► build_mock_draft()  → is_mock=True, labelled as mock
        │
        ▼
OutreachCampaign row (campaign_status = 'draft')
```

The prompt instructs the model to use only the supplied prospect facts and forbids placeholder
text, so a hallucinated company detail cannot reach a sales email.

---

## 6. Path to a full agent graph

| Step | Change needed | Effort |
| --- | --- | --- |
| 1 | Wrap each service as a LangGraph node with a typed state | Small - the services already return typed schemas |
| 2 | Add a conditional edge: if the score is below a threshold, request more research | Small |
| 3 | Add a research node that enriches a lead with external company data | Medium - needs a data source |
| 4 | Add an evaluation node that checks the generated email against the grounding rule | Medium |
| 5 | Persist the full graph trace per lead in a new `agent_runs` table | Small - follows the existing migration pattern |

None of these are required for Milestone 1; the pipeline boundary described in section 2 is the
contract that keeps them cheap.

---

## 7. Design decisions and trade-offs

| Decision | Rationale | Cost |
| --- | --- | --- |
| Deterministic pipeline instead of an agent graph | Auditable, testable, fast, no model dependency for core value | Less flexibility in multi-step reasoning |
| Rule-based score instead of a trained model | No labelled outcome data exists yet; a transparent heuristic is honest about its limits | Score is not a conversion probability |
| Sector reference table instead of live web research | No external data source is configured in this scope; keeps results reproducible | Insights are generic per sector |
| Mock fallback for the LLM | Keeps the platform runnable and demonstrable without credentials | Mock output is not AI output - always labelled |
| Drafts stored with status `draft` | No sending workflow exists, so `sent` would be a false claim | Drafts must be sent manually |
