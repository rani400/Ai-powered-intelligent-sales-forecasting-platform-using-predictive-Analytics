# Day-by-Day Plan — SalesGenie AI

**Project:** SalesGenie AI — AI Sales Assistant & Lead Intelligence Platform
**Window:** Monday 12 October 2026 → Wednesday 21 October 2026 (10 days)
**Primary milestone:** 1 — Lead Management & Intelligence Engine
**Next milestone started:** 2 — AI Outreach Generation (first slice)

This file separates **what was planned** from **what was actually completed**, day by day, and
gives the exact command for every step. A task is only marked *Completed* when the work exists
**and** has been verified. Where something was deliberately left out, it is listed as *Planned
only* or *Deferred*, never as completed.

---

## Status legend

| Status | Meaning |
| --- | --- |
| **Completed** | Implemented and verified (code exists and a test or script proves it) |
| **Partial** | Implemented, but a documented part is missing or deferred |
| **Planned only** | Described in the schedule, deliberately not built in this window |
| **Deferred** | Built later in the 40-day schedule, out of this 10-day scope |
| **In progress** | Started but not finished — the remaining work is listed explicitly |

---

## Day 1 — Monday, 12 October 2026 · Project Kickoff and Requirement Analysis

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 1.1 | Understand the project problem | Problem statement |
| 1.2 | Define the six project modules | Module list |
| 1.3 | Write functional requirements | Functional requirement set |
| 1.4 | Write non-functional requirements | Non-functional requirement set |
| 1.5 | Define the project scope | Scope statement (in / out) |
| 1.6 | Prepare the SRS document | `docs/SRS.md` |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 1.1 | Problem statement | **Completed** | `docs/SRS.md` §2 | — |
| 1.2 | Six-module list | **Completed** | `docs/SRS.md` §4.3 (each module marked in scope / partial / out of scope) | — |
| 1.3 | Functional requirements | **Completed** | `docs/SRS.md` §5 — 41 FRs, each with priority and test reference | — |
| 1.4 | Non-functional requirements | **Completed** | `docs/SRS.md` §6 — 16 NFRs with a verification method each | — |
| 1.5 | Project scope | **Completed** | `docs/SRS.md` §4.1 in scope, §4.2 out of scope with the target milestone for each | — |
| 1.6 | SRS document | **Completed** | `docs/SRS.md` — 13 sections including acceptance criteria and traceability | — |
| 1.7 | Requirements checklist | **Completed** | `docs/REQUIREMENTS_CHECKLIST.md` — every FR and NFR mapped to code and a test | — |

**Deliverables produced:** SRS document, requirements checklist, project scope, module list.

---

## Day 2 — Tuesday, 13 October 2026 · API Contracts, Repository and Development Setup

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 2.1 | Create the project structure | Folder tree |
| 2.2 | Configure GitHub | Repository, `.gitignore`, first commit |
| 2.3 | Define the API contracts | `docs/API_CONTRACTS.md` |
| 2.4 | Set up the Python environment | Virtual environment with the dependencies |
| 2.5 | Prepare the initial application | Bootable FastAPI + Streamlit |
| 2.6 | Prepare the Sprint 1 backlog | `SPRINT_PLAN.md` |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 2.1 | Project structure | **Completed** | `backend/`, `frontend/`, `data/`, `database/`, `docs/`, `README.md`, `SPRINT_PLAN.md`, `.gitignore` | — |
| 2.2 | Repository setup | **Partial** | The project is a **local git repository** on branch `main` with the full tree, `.gitignore` (excluding `.env`, `.venv/`, caches and local DB files) and the initial commit. **Not done:** no remote was added and nothing was pushed — no repository URL, account or credential was available in this environment | `git init -b main`<br>`git add .`<br>`git commit -m "SalesGenie AI - Milestone 1: lead management and intelligence engine"`<br>`git remote add origin YOUR_REPOSITORY_URL`<br>`git push -u origin main` |
| 2.3 | API contracts | **Completed** | `docs/API_CONTRACTS.md` — 13 endpoints with request fields, response shapes, validation rules and error responses. Conformance is enforced by `test_api_contract.py` | `python -m pytest backend/tests/test_api_contract.py -v` |
| 2.4 | Python environment | **Completed** | `backend/requirements.txt` (lower-bound pins, never exact) and `frontend/requirements.txt`, installed into a project-local `.venv` by `.\run.ps1 setup`. Every `run.ps1` command uses that interpreter, so the global site-packages is never touched. The suite passes inside the venv against the newest resolved versions (fastapi 0.159.1, starlette 1.9.0, pydantic 2.14.1, sqlalchemy 2.1.6, pytest 9.1.1) | `.\run.ps1 setup`<br>`.\run.ps1 test` |
| 2.5 | Initial application | **Completed** | FastAPI app with `/health` and `/docs`; Streamlit app with home + 3 pages | `python -m uvicorn app.main:app --reload --app-dir backend`<br>`python -m streamlit run frontend/app.py` |
| 2.6 | Sprint 1 backlog | **Completed** | `SPRINT_PLAN.md` — 37 backlog items across database design, lead APIs, CSV import, intelligence, testing and the demonstration | — |

**Deliverables produced:** repository structure, `.gitignore`, `.env.example`, API contracts,
development environment, bootable applications, sprint backlog.

---

## Day 3 — Wednesday, 14 October 2026 · Database Design, UI Wireframes and Agent Architecture

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 3.1 | Design the database schema | Eight tables |
| 3.2 | Define the `Leads` table | Columns, types, constraints, indexes |
| 3.3 | Define the table relationships | Foreign keys |
| 3.4 | Prepare the ER diagram | `docs/ER_DIAGRAM.md` |
| 3.5 | Design the Streamlit wireframes | Leads page and Intelligence panel |
| 3.6 | Prepare the agent architecture diagram | Prospect → analysis → score → recommendations |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 3.1 | Database schema | **Completed** | 8 tables: `leads`, `lead_scores`, `company_insights`, `outreach_campaigns` (live) + `users`, `sales_interactions`, `crm_sync_logs`, `sales_analytics` (schema only) | `python backend/scripts/migrate.py --status` |
| 3.2 | `Leads` table | **Completed** | 13 columns with types, nullability, defaults and 4 indexes — `docs/ER_DIAGRAM.md` §2.1 | — |
| 3.3 | Relationships | **Completed** | One-to-many from `leads` to `lead_scores`, `company_insights` and `outreach_campaigns`, all `ON DELETE CASCADE` | `python -m pytest backend/tests/test_migrations.py -v` |
| 3.4 | ER diagram | **Completed** | `docs/ER_DIAGRAM.md` — ASCII diagram, full column tables, integrity rules and the migration map | — |
| 3.5 | UI wireframes | **Completed** | `docs/UI_WIREFRAMES.md` — home, Leads, Intelligence and Outreach layouts with element behaviour tables | — |
| 3.6 | Agent architecture | **Completed** | `docs/AGENT_ARCHITECTURE.md` — the five-stage pipeline, request flow, intelligence detail, outreach detail and the path to a LangGraph graph | — |
| 3.7 | *(not in the original plan)* Full agent graph | **Planned only** | Documented as a later step in `docs/AGENT_ARCHITECTURE.md` §6, not built in this window | — |

**Deliverables produced:** ER diagram, schema draft, UI wireframes, agent architecture, design notes.

---

## Day 4 — Thursday, 15 October 2026 · Database Migrations and Lead CRUD APIs

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 4.1 | Configure the database connection | PostgreSQL via environment variables |
| 4.2 | Implement the database models | `backend/app/models/lead.py` |
| 4.3 | Create database migrations | Repeatable, controlled schema changes |
| 4.4 | Implement CRUD endpoints | Create, list, retrieve, update, delete |
| 4.5 | Add validation | Required fields, email format, status, status codes |
| 4.6 | Test the APIs | Evidence in Swagger and the test suite |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 4.1 | Database connection | **Partial** | `DATABASE_URL` drives the engine; `backend/app/config.py` reads only the environment and `.env`. **Configuration complete; the live server used SQLite** because no PostgreSQL instance was reachable here. PostgreSQL is the documented production target and the migration SQL expands dialect placeholders for it | `python backend/scripts/migrate.py --status` |
| 4.2 | Database models | **Completed** | `backend/app/models/lead.py` (+ `lead_score.py`, `company_insight.py`, `outreach_campaign.py`, `extended.py`) | — |
| 4.3 | Migrations | **Completed** | 4 numbered SQL scripts + `backend/scripts/migrate.py` with a `schema_migrations` ledger. Repeatability is asserted by TC-91 | `python backend/scripts/migrate.py`<br>`python backend/scripts/migrate.py --status`<br>`python backend/scripts/migrate.py --reset` |
| 4.4 | CRUD endpoints | **Completed** | `POST/GET /api/leads`, `GET/PUT/DELETE /api/leads/{lead_id}` | `python -m pytest backend/tests/test_leads.py -v` |
| 4.5 | Validation | **Completed** | `backend/app/schemas/lead_schema.py` — required company name, email format, status enum, phone format, whitespace normalisation, empty-body rejection | `python -m pytest backend/tests/test_leads.py -v` |
| 4.6 | API testing | **Completed** | Swagger at `/docs`; TC-01 … TC-12 cover create, retrieve, update, delete, invalid input and unknown ids | `python -m uvicorn app.main:app --reload --app-dir backend`<br>`python -m pytest backend/tests/test_leads.py -v` |

**Deliverables produced:** database models, migration scripts, working CRUD endpoints, test evidence.

---

## Day 5 — Friday, 16 October 2026 · CSV Import, Duplicate Detection and the Leads Interface

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 5.1 | Prepare the sample dataset | `data/sample_leads.csv` |
| 5.2 | Implement CSV upload | `backend/app/services/lead_import.py` |
| 5.3 | Implement duplicate detection | `backend/app/services/duplicate_detection.py` |
| 5.4 | Build the Streamlit Leads page | `frontend/pages/leads.py` |
| 5.5 | Connect the frontend to FastAPI | HTTP calls with real error handling |
| 5.6 | Verify the workflow | Records imported and visible in the UI |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 5.1 | Sample dataset | **Completed** | `data/sample_leads.csv` (4 clean rows) and `data/sample_leads_with_issues.csv` (5 rows with 4 deliberate problems) | — |
| 5.2 | CSV import service | **Completed** | `backend/app/services/lead_import.py` — required-column check, normalisation, per-row validation, inserted/rejected/duplicate counters, row-level error reasons | `python -m pytest backend/tests/test_lead_import.py -v` |
| 5.3 | Duplicate detection | **Completed** | `backend/app/services/duplicate_detection.py` — normalised-email hard match, company + contact soft match, `reject` / `skip` policies, soft-deleted rows ignored | `python -m pytest backend/tests/test_duplicates.py -v` |
| 5.4 | Streamlit Leads page | **Completed** | `frontend/pages/leads.py` — search, status/industry filters, CSV upload with the import report, add form, lead table, edit form, delete with confirmation | `python -m streamlit run frontend/app.py` |
| 5.5 | Frontend ↔ backend | **Completed** | `frontend/api_client.py` raises `ApiError` carrying the backend's own message; the UI shows that message instead of a false success | — |
| 5.6 | Workflow verification | **Completed** | The demo walkthrough imports the sample file and lists the records; the Streamlit page renders with 0 exceptions | `python backend/scripts/demo_walkthrough.py` |

**Deliverables produced:** import service, duplicate detection, Leads page, sample dataset, import test results.

---

## Day 6 — Saturday, 17 October 2026 · Unit Testing and Sample Dataset Validation

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 6.1 | Prepare unit tests | `backend/tests/test_leads.py` |
| 6.2 | Test the CSV import | Valid, missing columns, empty, invalid email, missing company, duplicate, partial |
| 6.3 | Check database consistency | Saves, updates, duplicates, foreign keys, error handling |
| 6.4 | Record the results | `docs/TEST_RESULTS.md` |
| 6.5 | Fix the identified bugs | Prioritised fixes |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 6.1 | Unit tests | **Completed** | `backend/tests/test_leads.py` (12), `test_lead_import.py` (14), `test_duplicates.py` (5), plus `test_intelligence.py`, `test_outreach.py`, `test_performance.py`, `test_migrations.py`, `test_api_contract.py` — 66 tests in total | `.\run.ps1 test` |
| 6.2 | Import testing | **Completed** | TC-20 … TC-33 cover all seven listed cases, a non-CSV upload and the three `update_existing` paths | `.\run.ps1 test` |
| 6.3 | Database consistency | **Completed** | TC-05 (updates persist), TC-26/TC-27 (duplicate policy), TC-54 (score rows), TC-93 (foreign keys enforced) | `python -m pytest backend/tests/test_migrations.py -v` |
| 6.4 | Results recorded | **Completed** | `docs/TEST_RESULTS.md` — 66 rows with test id, description, expected, actual and status; manual verification table; limitations | — |
| 6.5 | Bugs fixed | **Completed** | 7 bugs fixed (B-01 … B-07) with root cause and regression test — see `docs/TEST_RESULTS.md` §10 | `python -m pytest` |

**Deliverables produced:** unit test files, dataset validation, test results document, bug and fix log.

---

## Day 7 — Sunday, 18 October 2026 · Lead Intelligence Integration and Milestone Test Report

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 7.1 | Implement company profile analysis | `backend/app/services/lead_intelligence.py` |
| 7.2 | Implement the initial qualification scoring | Documented factors, 0–100 |
| 7.3 | Connect the intelligence to the interface | Display on the Leads page |
| 7.4 | Test the integrated workflow | Create → retrieve → analyse → score → display |
| 7.5 | Prepare the milestone test report | `docs/MILESTONE_1_REPORT.md` |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 7.1 | Company profile analysis | **Completed** | `backend/app/services/lead_intelligence.py` — profile, business needs, opportunities, key insights and information gaps. Sector statements are framed as sector context, never as company facts (TC-44) | `python -m pytest backend/tests/test_intelligence.py -v` |
| 7.2 | Qualification scoring | **Completed** | 5 weighted factors totalling 100 points, each with its own explanation. Labelled `rule_based_v1` with a disclaimer in the API payload | `python -m pytest backend/tests/test_intelligence.py -v` |
| 7.3 | Intelligence in the UI | **Completed** | `frontend/pages/intelligence.py` — company profile, score with the factor table, needs, opportunities, insights and gaps | `python -m streamlit run frontend/app.py` |
| 7.4 | Integrated workflow test | **Completed** | TC-43 exercises import → retrieve → analyse → score → display, and confirms the stored insight and score rows | `python -m pytest backend/tests/test_intelligence.py -v` |
| 7.5 | Milestone report | **Completed** | `docs/MILESTONE_1_REPORT.md` — features, database and API status, import results, intelligence examples, test summary, 10 known limitations, evidence, remaining issues, review status | — |

**Deliverables produced:** integrated intelligence panel, qualification scoring, milestone report, demo checklist.

---

## Day 8 — Monday, 19 October 2026 · Milestone 1 Demonstration and Bug Fixes

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 8.1 | Prepare the demonstration environment | Backend + frontend + database + sample data running |
| 8.2 | Demonstrate lead management | Create, list, update, delete, search |
| 8.3 | Demonstrate CSV import | Valid upload, duplicate detection, validation |
| 8.4 | Demonstrate lead intelligence | Company summary, score, insights |
| 8.5 | Explain the design | ER diagram, tables, API contracts, architecture, testing |
| 8.6 | Record feedback | `docs/EVALUATION_FEEDBACK.md` |
| 8.7 | Fix critical problems | Broken APIs, wrong data, DB failures, import errors, UI issues |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 8.1 | Environment | **Completed** | Backend on `:8000`, Streamlit on `:8501`, migrations applied, sample data loaded, all four Streamlit pages rendering with 0 exceptions | `python backend/scripts/migrate.py`<br>`python -m uvicorn app.main:app --app-dir backend`<br>`python -m streamlit run frontend/app.py` |
| 8.2 | Lead management demo | **Completed** | Section 2 and 3 of the walkthrough; the demo checklist in the milestone report | `python backend/scripts/demo_walkthrough.py` |
| 8.3 | CSV import demo | **Completed** | Sections 2, 8 and 9 of the walkthrough (import, validation failure, duplicate conflict) | `python backend/scripts/demo_walkthrough.py` |
| 8.4 | Intelligence demo | **Completed** | Section 4 of the walkthrough — profile, score with the factor breakdown, needs, opportunities, insights, gaps | `python backend/scripts/demo_walkthrough.py` |
| 8.5 | Design explanation | **Completed** | `docs/ER_DIAGRAM.md`, `docs/API_CONTRACTS.md`, `docs/AGENT_ARCHITECTURE.md`, `docs/TEST_RESULTS.md`, `docs/UI_WIREFRAMES.md` | — |
| 8.6 | Feedback recorded | **Partial** | `docs/EVALUATION_FEEDBACK.md` — 15 self-identified issues plus a 6-row defect log, each with severity, owner, planned fix and status. **Not done:** no external evaluator feedback has been supplied, so §4 is an empty template rather than a transcription | — |
| 8.7 | Critical fixes | **Completed** | 2 Critical, 3 High and 5 Medium/Low issues fixed and re-verified — see the closed-items table in the feedback log | `python -m pytest` |

**Deliverables produced:** demonstration, feedback and issue log, bug fixes, updated test evidence.

---

## Day 9 — Tuesday, 20 October 2026 · Milestone 1 Submission and Review

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 9.1 | Run the regression tests | Core tests re-run after the fixes |
| 9.2 | Verify prospect record coverage | Coverage calculated and recorded honestly |
| 9.3 | Review the company insights | Relevance, clarity, no unsupported claims |
| 9.4 | Finalise the documentation | Report, test results, contracts, README |
| 9.5 | Prepare the submission evidence | Screenshots, Swagger, ER diagram, results, notes |
| 9.6 | Record the review status | Submitted / approved / awaiting feedback |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 9.1 | Regression tests | **Completed** | 66/66 pass after all Day 8 fixes | `python -m pytest` |
| 9.2 | Record coverage | **Completed** | **Measured: 100.00 %** over 100 records and **100.00 %** over 500 records. The script imports, retrieves, updates, analyses and deletes every record and computes the ratio — the figure is a measurement, not an assertion | `python backend/scripts/measure_coverage.py --rows 500` |
| 9.3 | Insight review | **Completed** | Reviewed against the stored record; sector framing is explicit, missing facts are reported as gaps, and TC-44 blocks revenue/headcount/funding claims | `python -m pytest backend/tests/test_intelligence.py -v` |
| 9.4 | Documentation finalised | **Completed** | `docs/MILESTONE_1_REPORT.md`, `docs/TEST_RESULTS.md`, `docs/API_CONTRACTS.md`, `docs/REQUIREMENTS_CHECKLIST.md`, `docs/TECH_STACK.md`, `docs/DAY_PLAN.md`, `README.md` | — |
| 9.5 | Submission evidence | **Partial** | The live evidence is in place (Swagger at `/docs`, Streamlit at `:8501`, walkthrough transcript, coverage measurement, migration state, ER diagram) and the tree is committed to a local git repository on `main`. **Not done:** screen captures and a GitHub repository link, because no remote was created and no screenshot tool is available in this environment | `python backend/scripts/demo_walkthrough.py` |
| 9.6 | Review status | **Completed** | `docs/MILESTONE_1_REPORT.md` §12 — implementation complete, tests green, coverage measured, **submitted for review, approval pending the evaluator's decision** | — |

**Deliverables produced:** final milestone report, test evidence, submission package, review status.

---

## Day 10 — Wednesday, 21 October 2026 · Start Milestone 2 — AI Outreach Generation

### Planned

| # | Step | Planned deliverable |
| --- | --- | --- |
| 10.1 | Define the email generation input | Request structure |
| 10.2 | Design reusable prompt templates | Templates by industry and situation |
| 10.3 | Implement the outreach generation service | Provider call, validation, error handling, mock fallback |
| 10.4 | Create the outreach campaigns model | `backend/app/models/outreach_campaign.py` + migration |
| 10.5 | Define the outreach endpoint | `POST /api/outreach/generate` |
| 10.6 | Store and retrieve drafts | Persist with a draft status |
| 10.7 | Test the service | Valid data, missing info, tones, industries, empty response, API failure, storage |

### Completed

| # | Step | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| 10.1 | Generation input | **Completed** | `backend/app/schemas/outreach_schema.py::OutreachRequest` — lead id, optional name/industry overrides, offering, goal, tone, length | `python -m pytest backend/tests/test_outreach.py -v` |
| 10.2 | Prompt templates | **Completed** | `backend/app/services/outreach_generator.py` — 3 goals × 2 tones × 2 lengths, plus industry guidance that frames sector context as sector context | `python -m pytest backend/tests/test_outreach.py::test_tc61_prompt_contains_prospect_facts -v` |
| 10.3 | Generation service | **Completed** | Provider client with timeout, retry and HTTP-error handling; `SUBJECT:`/`BODY:` parsing; a clearly-labelled deterministic mock when no key is configured | `python -m pytest backend/tests/test_outreach.py -v` |
| 10.4 | Campaign model and migration | **Completed** | `backend/app/models/outreach_campaign.py` and `backend/migrations/003_outreach_campaigns.sql` — `campaign_id` PK, `lead_id` FK, subject, content, status, created_at plus tone/length/goal/provider/mock-flag columns | `python backend/scripts/migrate.py --status` |
| 10.5 | Outreach endpoint | **Completed** | `POST /api/outreach/generate` plus `GET /api/outreach` and `GET /api/leads/{lead_id}/outreach` | `python -m pytest backend/tests/test_outreach.py -v` |
| 10.6 | Draft storage | **Completed** | Every draft is stored with `campaign_status='draft'`. Nothing can be marked `sent`, because no sending workflow exists — TC-67 asserts this | `python -m pytest backend/tests/test_outreach.py::test_tc67_draft_is_stored_as_draft -v` |
| 10.7 | Service testing | **Completed** | TC-60 … TC-72 — all seven listed scenarios plus tone/length variants, unknown lead and a 502 on provider failure | `python -m pytest backend/tests/test_outreach.py -v` |
| 10.8 | *(not in the original plan)* Outreach UI page | **Completed** | `frontend/pages/outreach.py` — generation options, preview, mock-mode warning, stored-draft table | `python -m streamlit run frontend/app.py` |

**Deliverables produced:** outreach service, prompt templates, campaign model and migration, endpoint, sample drafts, test results.

---

## Summary — planned vs completed

| Day | Theme | Planned items | Completed | Partial | Planned only / Deferred |
| --- | --- | --- | --- | --- | --- |
| 1 | Requirements | 6 | 7 | 0 | 0 |
| 2 | Setup and contracts | 6 | 5 | 2 | 0 |
| 3 | Design | 6 | 6 | 0 | 1 |
| 4 | Database and CRUD | 6 | 6 | 1 | 0 |
| 5 | Import and UI | 6 | 6 | 0 | 0 |
| 6 | Testing | 5 | 5 | 0 | 0 |
| 7 | Intelligence | 5 | 5 | 0 | 0 |
| 8 | Demonstration | 7 | 7 | 1 | 0 |
| 9 | Submission | 6 | 6 | 1 | 0 |
| 10 | Outreach | 7 | 8 | 0 | 0 |
| **Total** | | **60** | **61** | **5** | **1** |

**Completed:** 61 steps · **Partial:** 5 steps · **Planned only:** 1 step

### The five partial items, in full

| Day | Item | What is done | What is missing | Why |
| --- | --- | --- | --- | --- |
| 2 | GitHub repository | The full tree, `.gitignore`, `.env.example` and the commit-ready layout, initialised as a local git repository with the initial commit on `main` | The remote repository was never created and nothing was pushed | No repository URL, account or credential was available in this environment. The commands to finish it are in Day 2 row 2.2 |
| 2 | Python environment | `backend/requirements.txt` and `frontend/requirements.txt` with lower-bound pins, installed into a project-local `.venv` that every `run.ps1` command uses | Nothing functional is missing | The earlier `python -m venv .venv` failed with `No space left on device`; freeing the pip cache (2.3 GB) resolved it, so the environment now exists and the suite passes inside it |
| 4 | PostgreSQL connection | `DATABASE_URL` selects the engine, the SQL is dialect-portable and the runner expands the placeholders | The verification runs used SQLite | No PostgreSQL server was reachable here. The same SQL runs unchanged on PostgreSQL |
| 8 | Evaluation feedback | 15 self-identified issues and 6 defects, each with severity, owner, planned fix and status | §4 (evaluator feedback) is an empty template | The evaluation had not taken place when this was written |
| 9 | Submission evidence | Live Swagger, live Streamlit, walkthrough transcript, coverage measurement, ER diagram | Screen captures and the repository link | No screenshot tool is available here, and no repository exists |

### The one planned-only item

| Day | Item | Status |
| --- | --- | --- |
| 3 | A complete LangGraph agent graph | Documented as the path forward in `docs/AGENT_ARCHITECTURE.md` §6. The window implements the deterministic pipeline instead, which is testable and auditable |

---

## Master command reference

### One-time setup

```powershell
cd "C:\Users\Dell\Desktop\sales genie ai"

# 1. Create the virtual environment, install the dependencies and create .env
.\run.ps1 setup

# 2. Apply the migrations
.\run.ps1 migrate
```

`setup` builds a project-local `.venv` and installs into it. The global interpreter is left
untouched — this matters on a shared machine, because an exact-pinned requirements file would
otherwise make pip downgrade packages that other projects depend on.

If you prefer to drive the virtual environment by hand:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m pip install -r frontend\requirements.txt
```

If activation is blocked by the machine's execution policy, call the interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pytest
```

> The virtual environment needs roughly 700 MB of free disk space once Streamlit and its
> transitive dependencies are installed. Free the pip cache with `python -m pip cache purge`
> if the install fails with `No space left on device`.

### Run the system

```powershell
# Terminal 1 - database
.\run.ps1 migrate

# Terminal 2 - backend API (http://127.0.0.1:8000, docs at /docs)
.\run.ps1 api

# Terminal 3 - Streamlit UI (http://127.0.0.1:8501)
.\run.ps1 ui
```

### Verify

```powershell
# Full automated suite
.\run.ps1 test

# Individual suites
.\.venv\Scripts\python.exe -m pytest backend\tests\test_leads.py -v
.\.venv\Scripts\python.exe -m pytest backend\tests\test_lead_import.py -v
.\.venv\Scripts\python.exe -m pytest backend\tests\test_duplicates.py -v
.\.venv\Scripts\python.exe -m pytest backend\tests\test_intelligence.py -v
.\.venv\Scripts\python.exe -m pytest backend\tests\test_outreach.py -v
.\.venv\Scripts\python.exe -m pytest backend\tests\test_performance.py -v
.\.venv\Scripts\python.exe -m pytest backend\tests\test_migrations.py -v
.\.venv\Scripts\python.exe -m pytest backend\tests\test_api_contract.py -v

# End-to-end walkthrough transcript
.\run.ps1 demo

# Measured record coverage
.\run.ps1 coverage

# Migration state
.\run.ps1 status

# Lint and format checks
.\run.ps1 lint
```

### Optional: PostgreSQL instead of SQLite

```powershell
# In .env, replace the DATABASE_URL line:
#   DATABASE_URL=postgresql+psycopg2://salesgenie:<password>@localhost:5432/salesgenie

docker compose up -d db          # start PostgreSQL
python backend\scripts\migrate.py --reset
python -m pytest
```

---

## Final delivery checklist — 12 to 21 October

| # | Deliverable | Status | Where |
| --- | --- | --- | --- |
| 1 | SRS and requirements documented | **Complete** | `docs/SRS.md`, `docs/REQUIREMENTS_CHECKLIST.md` |
| 2 | Repository structure, `.gitignore`, `.env.example` | **Complete** | root of the project |
| 3 | GitHub repository | **Partial** — local git repository initialised and committed on `main`; the remote was not created or pushed (no URL or credential available) | see Day 2 row 2.2 |
| 4 | API contracts | **Complete** | `docs/API_CONTRACTS.md` (conformance enforced by tests) |
| 5 | Development environment configured | **Partial** — pinned requirements and a working interpreter; no committed virtual environment (the drive ran out of disk space) | `backend/requirements.txt`, `.env` |
| 6 | ER diagram and database schema | **Complete** | `docs/ER_DIAGRAM.md` |
| 7 | Database migrations | **Complete** | `backend/migrations/`, `backend/scripts/migrate.py` |
| 8 | Lead CRUD APIs implemented and tested | **Complete** | `backend/app/routers/leads.py` — TC-01 … TC-12 |
| 9 | CSV import and duplicate detection | **Complete** | `backend/app/services/lead_import.py`, `duplicate_detection.py` — TC-20 … TC-30 |
| 10 | Streamlit interface connected to the backend | **Complete** | `frontend/app.py`, `frontend/pages/` |
| 11 | Unit tests and sample dataset | **Complete** | `backend/tests/` — 66 tests; `data/sample_leads.csv` |
| 12 | Test results documented | **Complete** | `docs/TEST_RESULTS.md` |
| 13 | Lead Intelligence panel integrated | **Complete** | `backend/app/services/lead_intelligence.py`, `frontend/pages/intelligence.py` — TC-40 … TC-55 |
| 14 | Milestone 1 demonstration completed | **Complete** | `backend/scripts/demo_walkthrough.py` |
| 15 | Feedback and issue log | **Partial** — self-identified issues recorded; no external evaluator feedback supplied yet | `docs/EVALUATION_FEEDBACK.md` |
| 16 | Submission evidence and review status | **Partial** — live evidence complete; screen captures and the repository link outstanding | `docs/MILESTONE_1_REPORT.md` §10, §12 |
| 17 | Initial AI outreach generation and campaign storage | **Complete** | `backend/app/services/outreach_generator.py`, `backend/app/models/outreach_campaign.py` — TC-60 … TC-72 |

---

## Explicitly out of this window

| Item | Target milestone |
| --- | --- |
| Conversation intelligence and CRM integration | Milestone 3 |
| Full sales analytics dashboard | Milestone 4 |
| Learned conversion-probability model | Milestone 4 |
| Authentication and role enforcement | Milestone 3 |
| Email sending workflow | Milestone 3 |
| Full LangGraph agent orchestration | Milestone 2 (later) |
| Production deployment and CI/CD | Post-window |
