# Software Requirements Specification (SRS)
## SalesGenie AI – AI Sales Assistant & Lead Intelligence Platform

| Field | Value |
| --- | --- |
| Document version | 1.0 |
| Status | Baseline for Milestone 1 (Lead Management & Intelligence Engine) |
| Date | 12 October 2026 (plan baseline) |
| Scope window | 12 Oct 2026 – 21 Oct 2026 |

---

## 1. Introduction

SalesGenie AI is an AI-assisted sales platform that reduces the manual effort sales teams spend on
prospect data entry, company research, lead qualification and first-touch outreach drafting.

This SRS defines the requirements for the 10-day delivery window that starts with **Milestone 1 –
Lead Management & Intelligence Engine** and opens with the first slice of **Milestone 2 – AI
Outreach Generation**.

The document is written so that every requirement is traceable to an implementation and a test.

### 1.1 Purpose

Define what the system must do, what quality it must meet, and which parts are explicitly out of
scope for this delivery window.

### 1.2 Definitions

| Term | Meaning |
| --- | --- |
| Prospect / Lead | A company plus a named contact that the sales team may approach |
| Lead Intelligence | Structured, data-derived analysis of a prospect's company, needs and opportunities |
| Qualification score | A transparent 0–100 rule-based score indicating how complete/salient a prospect record is |
| Outreach campaign | A stored email draft generated for a lead |
| Eligible record | A prospect record that passes validation and is available for management and analysis |

---

## 2. Problem Statement

Sales representatives spend a large share of their week on non-selling work:

1. **Data entry** – prospect details arrive by email, spreadsheet and event lists and are re-typed.
2. **Research** – the rep manually searches for company size, industry and likely pain points.
3. **Qualification** – there is no consistent way to decide which prospects deserve attention now.
4. **Outreach drafting** – each first email is written from scratch, producing inconsistent tone.
5. **Duplicates** – the same company/contact is added multiple times, so reporting is wrong.

The outcome is slow lead handling, inconsistent messaging, and unreliable pipeline data.

SalesGenie AI addresses this with a single workflow:

```
Prospect data → Company analysis → Lead intelligence → Qualification score → Recommendations
```

## 3. Project Objectives

| ID | Objective | Measure of success |
| --- | --- | --- |
| OBJ-1 | Centralise prospect records | 100% of accepted records stored centrally with validation |
| OBJ-2 | Remove manual CSV re-typing | Bulk import of a CSV with per-row success/rejection reporting |
| OBJ-3 | Prevent duplicate contamination | Duplicate emails are flagged/rejected, never silently inserted |
| OBJ-4 | Surface company insight | Every eligible record has a generated, source-grounded insight record |
| OBJ-5 | Provide repeatable prioritisation | Every eligible record has a documented 0–100 score with visible factors |
| OBJ-6 | Draft first-touch outreach | A lead + preferences produces a stored, reviewable email draft |

## 4. Project Scope

### 4.1 In scope (12 Oct – 21 Oct 2026)

- Lead Management & Prospect Database (CRUD + CSV import + duplicate detection + validation)
- Lead Intelligence & Company Analysis (company profile, needs, opportunities, gaps)
- Lead Scoring (transparent rule-based qualification score, 0–100)
- Initial AI Outreach Generation service + prompt templates + draft persistence
- Streamlit operator interface for the above
- Automated tests, test results, milestone report, demonstration evidence

### 4.2 Out of scope for this window

| Item | Reason | Planned stage |
| --- | --- | --- |
| Conversation Intelligence / summarisation | Later milestone in the 40-day schedule | Milestone 3+ |
| CRM integrations (Salesforce/HubSpot) | Requires external credentials and partner accounts | Milestone 3+ |
| Full Sales Analytics dashboard | Depends on pipeline volume and CRM data | Milestone 4 |
| Predictive conversion-probability ML model | Needs labelled outcome history; a rule-based baseline ships first | Milestone 4 |
| Complete multi-agent LangGraph orchestration | The flow is documented and implemented as a deterministic pipeline first | Milestone 2 (later) |
| Production deployment / CI-CD / container rollout | Out of the 10-day window | Post-window |

### 4.3 Module list (six modules from the project PDF)

| # | Module | Status in this window |
| --- | --- | --- |
| 1 | Lead Management & Prospect Database | **In scope — implemented** |
| 2 | Lead Intelligence & Company Analysis | **In scope — implemented (rule-based)** |
| 3 | AI Outreach Generation | **In scope — first slice (generation + storage)** |
| 4 | Lead Scoring & Recommendation Engine | **Partial** — transparent score implemented; learned model out of scope |
| 5 | Conversation Intelligence & CRM Integration | **Out of scope** — schema designed only |
| 6 | Dashboard & Sales Analytics | **Out of scope** — schema designed only; operational counters only |

## 5. Functional Requirements

### 5.1 Lead Management (Module 1)

| ID | Requirement | Priority | Verified by |
| --- | --- | --- | --- |
| FR-1.1 | System creates a lead with company name, industry, contact name, email, phone and lead status | Must | TC-01 |
| FR-1.2 | System lists leads with pagination, search and status filtering | Must | TC-02, TC-03 |
| FR-1.3 | System retrieves a single lead by ID | Must | TC-04 |
| FR-1.4 | System updates a lead without losing unrelated fields | Must | TC-05 |
| FR-1.5 | System deletes a lead and its dependent records | Must | TC-06 |
| FR-1.6 | System returns 404 with a clear body for an unknown lead ID | Must | TC-07 |
| FR-1.7 | System rejects invalid payloads with 422 and a field-level message | Must | TC-08, TC-09 |
| FR-1.8 | System imports leads from an uploaded CSV file | Must | TC-20 … TC-24 |
| FR-1.9 | System validates required CSV columns and rejects the file when they are absent | Must | TC-21 |
| FR-1.10 | System normalises email and whitespace on every write path | Must | TC-25 |
| FR-1.11 | System detects duplicate leads by normalised email, and flags company+contact pairs for review | Must | TC-26 … TC-28 |
| FR-1.12 | System reports per-row import outcomes (inserted / duplicate / rejected with reason) | Must | TC-29 |
| FR-1.13 | System records the lead source (manual vs csv_import) | Should | TC-02 |
| FR-1.14 | System stores a soft `is_active` flag and excludes deleted rows from listings | Should | TC-06 |

### 5.2 Lead Intelligence (Module 2)

| ID | Requirement | Priority | Verified by |
| --- | --- | --- | --- |
| FR-2.1 | System produces a company summary using only stored field values | Must | TC-40 |
| FR-2.2 | System produces an industry-specific opportunity list | Must | TC-41 |
| FR-2.3 | System produces a "information gaps" list when required fields are missing | Must | TC-42 |
| FR-2.4 | System persists each insight run as a dated `Company_Insights` row | Must | TC-43 |
| FR-2.5 | System never asserts company facts absent from the record (no invented revenue/headcount) | Must | TC-44 |
| FR-2.6 | System exposes insights over HTTP for a given lead | Must | TC-45 |
| FR-2.7 | System returns the latest insight set for a lead | Must | TC-46 |

### 5.3 Lead Scoring (Module 4, baseline)

| ID | Requirement | Priority | Verified by |
| --- | --- | --- | --- |
| FR-3.1 | System computes a 0–100 qualification score from documented factors | Must | TC-50 |
| FR-3.2 | System returns the individual factor contributions with the score | Must | TC-51 |
| FR-3.3 | System records every score in `Lead_Scores` with a timestamp | Must | TC-52 |
| FR-3.4 | System documents that the score is a rule-based baseline, not a conversion predictor | Must | docs |
| FR-3.5 | Score is deterministic for identical input | Must | TC-53 |

### 5.4 AI Outreach Generation (Module 3, first slice)

| ID | Requirement | Priority | Verified by |
| --- | --- | --- | --- |
| FR-4.1 | System accepts lead identity plus product/service, goal, tone and length preferences | Must | TC-60 |
| FR-4.2 | System builds the prompt from validated lead data and the selected template | Must | TC-61 |
| FR-4.3 | System calls the configured LLM provider and extracts subject + body | Must | TC-62 |
| FR-4.4 | System returns a clearly-labelled mock draft when no LLM is configured | Must | TC-63 |
| FR-4.5 | System handles provider timeout, provider error and empty response without a 500 | Must | TC-64, TC-65, TC-66 |
| FR-4.6 | System stores each generated draft in `Outreach_Campaigns` with status `draft` | Must | TC-67 |
| FR-4.7 | System retrieves stored drafts for a lead | Must | TC-68 |
| FR-4.8 | System never marks a draft as `sent` without a real sending workflow | Must | TC-67 |
| FR-4.9 | System supports tone (professional/friendly) and length (short/detailed) variants | Must | TC-69 |

### 5.5 Interface

| ID | Requirement | Priority | Verified by |
| --- | --- | --- | --- |
| FR-5.1 | Leads page provides search, filter, CSV upload, add form, table, edit, delete | Must | manual demo |
| FR-5.2 | Leads page surfaces backend error messages instead of showing false success | Must | manual demo |
| FR-5.3 | Intelligence panel shows company profile, score with factors, opportunities, insights, gaps | Must | manual demo |
| FR-5.4 | Outreach page generates, previews and stores drafts | Must | manual demo |

## 6. Non-Functional Requirements

| ID | Category | Requirement | Verification |
| --- | --- | --- | --- |
| NFR-1 | Data validation | All writes are validated at the API boundary; invalid email, missing company name or unknown status are rejected with 422 | TC-08, TC-09 |
| NFR-2 | Data integrity | Foreign keys are enforced; orphan rows cannot be created | TC-43 |
| NFR-3 | Reliability | Import is atomic per row — one bad row does not roll back good rows, and no partial/corrupt row is written | TC-23 |
| NFR-4 | Security | DB credentials live only in `.env`, which is git-ignored; `.env.example` documents the keys without values | repo audit |
| NFR-5 | Security | Contact data is never written to logs or printed to console in production paths | code audit |
| NFR-6 | Security | No secrets are committed; `.gitignore` covers `.env`, `venv`, caches and local DB files | repo audit |
| NFR-7 | Maintainability | Modular architecture: `routers` → `services` → `models`; business rules are not in route handlers | code audit |
| NFR-8 | Maintainability | Every public function has a docstring and type hints | code audit |
| NFR-9 | Maintainability | Configuration is externalised to environment variables, not hard-coded | code audit |
| NFR-10 | Error handling | A single exception-handling path converts domain errors into consistent JSON error bodies with correct HTTP codes | TC-07 |
| NFR-11 | Performance | List endpoint responds in < 500 ms for a 10,000-row dataset on the local benchmark | TC-80 |
| NFR-12 | Performance | Import of 1,000 rows completes in < 30 s | TC-81 |
| NFR-13 | Usability | Error messages state what failed and how to fix it, without stack traces | TC-09 |
| NFR-14 | Usability | The UI is usable without reading the source; primary actions are labelled | manual demo |
| NFR-15 | Testability | Core services (import, duplicate detection, intelligence, scoring, outreach) are unit-testable without a live server | pytest run |
| NFR-16 | Portability | PostgreSQL is the documented production target; SQLite is supported for local development and automated tests via `DATABASE_URL` | code audit |

## 7. Technology Stack

| Layer | Choice | Rationale |
| --- | --- | --- |
| Backend API | Python 3.11+ / FastAPI | Async-ready, auto OpenAPI docs, Pydantic validation |
| Validation | Pydantic v2 | Declarative schemas reused by API and services |
| ORM | SQLAlchemy 2.0 (declarative, typed) | Typed models, portable across PostgreSQL and SQLite |
| Database | PostgreSQL 14+ (production) / SQLite (dev + CI) | Transactional integrity, FK enforcement |
| Migrations | Versioned SQL scripts + a tracked runner (`backend/scripts/migrate.py`) | Repeatable, reviewable, engine-portable |
| CSV parsing | Python standard library `csv` module | No heavyweight dependency for correctness-critical parsing |
| Frontend | Streamlit | Fast operator UI, no separate build chain |
| AI | Provider-agnostic LLM client (OpenAI-compatible HTTP) with a labelled mock fallback | Keeps the platform runnable without credentials |
| Testing | pytest + httpx | Fast, isolated, CI-friendly |

See `docs/TECH_STACK.md` for the full rationale and version pinning.

## 8. User Roles

| Role | Responsibilities | Access in this window |
| --- | --- | --- |
| Sales Development Rep (primary user) | Import and maintain the prospect list, review intelligence, generate outreach drafts | Full access to every implemented endpoint and the Streamlit UI |
| Sales Manager | Review qualification scores, decide which leads to work first, approve outreach | Read access to leads, scores and insights; cannot delete leads |
| Platform Admin | Manage environment configuration, database and migrations | Access to `.env`/migrations, full API access |
| Evaluator / Reviewer | Verify Milestone 1 against acceptance criteria | Read access to the running system, test results and milestone report |

Authentication/roles are **not implemented** in this window — the API is open and role-based
authorisation is a later-stage item. This is recorded as a known limitation.

## 9. Initial Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend (frontend/)                    │
│   Leads page · Intelligence panel · Outreach page                    │
│         │  HTTP (requests)                                          │
└─────────┼────────────────────────────────────────────────────────────┘
          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (backend/app)                   │
│  routers/    leads.py · insights.py · outreach.py                   │
│  services/   lead_import · duplicate_detection · lead_intelligence  │
│              scoring · outreach_generator · prompts                  │
│  schemas/    pydantic request/response models                       │
│  models/     SQLAlchemy ORM (leads, lead_scores, company_insights,  │
│              outreach_campaigns)                                     │
│  database.py engine / session / Base          config.py settings     │
└─────────┬────────────────────────────────────────────────────────────┘
          ▼
   PostgreSQL (prod) / SQLite (dev, tests)
```

Request flow for a lead:

```
POST /api/leads → schema validation → service layer → ORM → DB
                                                    ↓
GET /api/leads/{id}/insights → lead_intelligence service
                               → Company_Insights + Lead_Scores rows
                               → JSON summary (profile, score, factors,
                                 opportunities, insights, gaps)
```

Agent / pipeline flow (module 2 → 4):

```
Prospect data → Company analysis → Lead intelligence → Qualification score → Recommendations
```

## 10. Expected Outcomes

1. A single source of truth for prospect records with enforced validation and referential integrity.
2. CSV ingestion that reports exactly what was accepted, skipped as duplicate, or rejected and why.
3. Every eligible prospect has a stored insight set and a transparent 0–100 score with visible factors.
4. A usable first-touch email draft per prospect, stored with the lead and marked `draft`.
5. A documented, reproducible test suite with recorded results and a Milestone 1 report.
6. An honest statement of what is *not* implemented, so later milestones start from a known baseline.

## 11. Acceptance Criteria for Milestone 1

| # | Criterion | Evidence |
| --- | --- | --- |
| AC-1 | CRUD APIs functional for create/read/update/delete | `docs/TEST_RESULTS.md`, Swagger at `/docs` |
| AC-2 | CSV import works with validation, normalisation and duplicate handling | `docs/TEST_RESULTS.md` §CSV import |
| AC-3 | ≥ 95 % of eligible prospect records are manageable and analysable | `docs/MILESTONE_1_REPORT.md` §Record coverage (measured) |
| AC-4 | Lead Intelligence displays company insights derived from the record | `docs/MILESTONE_1_REPORT.md` §Lead intelligence examples |
| AC-5 | Test suite passes and results are recorded | `docs/TEST_RESULTS.md` |
| AC-6 | Known limitations and remaining work are stated | `docs/MILESTONE_1_REPORT.md` §Known limitations |

## 12. Traceability

Requirement → implementation → test is maintained in `docs/TEST_RESULTS.md`, which lists the test
case ID used in this SRS against the executable test name and the recorded pass/fail outcome.

## 13. Revision History

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 1.0 | 12 Oct 2026 | SalesGenie team | Initial SRS for the 12–21 Oct window |
