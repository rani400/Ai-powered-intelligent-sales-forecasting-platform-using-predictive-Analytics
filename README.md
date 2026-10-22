# SalesGenie AI

**AI Sales Assistant & Lead Intelligence Platform**

A prospect database with validation and duplicate detection, company intelligence with a
transparent qualification score, and AI-drafted first-touch outreach — exposed through a FastAPI
backend and a Streamlit operator interface.

---

## Status

| Milestone | Scope | Status |
| --- | --- | --- |
| **1 — Lead Management & Intelligence Engine** | Lead CRUD, CSV import, duplicate detection, company insights, qualification score, UI | **Complete** — 66/66 tests pass |
| **2 — AI Outreach Generation (first slice)** | Prompt templates, provider-backed generation with a labelled mock fallback, draft storage | **Complete** |
| Later stages | CRM integration, conversation intelligence, full analytics dashboard, learned conversion model | **Not in this window** |---

## Quick start

```powershell
cd "C:\Users\Dell\Desktop\sales genie ai"

# 1. Virtual environment + dependencies + .env
.\run.ps1 setup

# 2. Database
.\run.ps1 migrate
```

Then start the two processes in **separate terminals**:

```powershell
# Terminal 1 - Backend API -> http://127.0.0.1:8000  (docs at /docs)
.\run.ps1 api

# Terminal 2 - Frontend    -> http://127.0.0.1:8501
.\run.ps1 ui
```

`run.ps1` always uses `.venv\Scripts\python.exe` when that environment exists, so the project
never installs into the global interpreter.

### Running without the helper script

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend
.\.venv\Scripts\python.exe -m streamlit run frontend\app.py
```

### Dependencies

`setup` installs two requirement files into `.venv`:

| File | Packages |
| --- | --- |
| `backend/requirements.txt` | `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pydantic-settings`, `python-dotenv`, `python-multipart`, `httpx`, `psycopg2-binary`, `pytest`, `pytest-cov` |
| `frontend/requirements.txt` | `streamlit`, `requests` |

Both files use **lower bounds** (`>=`), not exact pins. Exact pins make pip downgrade packages
that are already installed, which breaks unrelated projects sharing the same interpreter.

### Verify the installation

```powershell
.\run.ps1 test       # expect: 66 passed
```

### Helper script

`run.ps1` wraps the common commands:

```powershell
.\run.ps1 setup      # create .venv, install dependencies, create .env
.\run.ps1 migrate    # apply pending migrations
.\run.ps1 status     # show the migration state
.\run.ps1 test       # run the test suite
.\run.ps1 api        # start the backend on :8000
.\run.ps1 ui         # start the Streamlit UI on :8501
.\run.ps1 demo       # end-to-end walkthrough transcript
.\run.ps1 coverage   # measure record coverage
.\run.ps1 lint       # ruff lint + format check
.\run.ps1 check      # tests + migrations + a live API check
```

The API and the UI need separate terminals.

---

## What it does

| Capability | Endpoint | Where in the UI |
| --- | --- | --- |
| Manage prospect records | `POST/GET/PUT/DELETE /api/leads`, `GET /api/leads/{id}` | **Leads** page |
| Import a prospect list from CSV | `POST /api/leads/import` | **Leads** page → Import |
| Detect duplicates | email hard match, company + contact soft match | Shown per row in the import report |
| Analyse a prospect | `GET /api/leads/{id}/insights` | **Intelligence** page |
| Score a prospect (0–100) | same endpoint, `qualification_score` | **Intelligence** page |
| Draft a first-touch email | `POST /api/outreach/generate` | **Outreach** page |
| Review stored drafts | `GET /api/outreach`, `GET /api/leads/{id}/outreach` | **Outreach** page |
| Dashboard counters | `GET /api/leads/stats` | Home page |

---

## Project layout

```
salesgenie-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                     FastAPI application entry point
│   │   ├── config.py                   Environment-driven settings
│   │   ├── database.py                 Engine, session factory, declarative base
│   │   ├── errors.py                   Domain errors and the shared error envelope
│   │   ├── models/                     lead, lead_score, company_insight,
│   │   │                               outreach_campaign, extended
│   │   ├── schemas/                    lead_schema, outreach_schema
│   │   ├── routers/                    leads, company_analysis, outreach
│   │   ├── services/                   lead_service, lead_import,
│   │   │                               duplicate_detection, lead_intelligence,
│   │   │                               outreach_generator
│   │   └── utils/                      validation helpers
│   ├── migrations/                     001 … 004 versioned SQL scripts
│   ├── scripts/                        migrate, demo_walkthrough, measure_coverage
│   ├── tests/                          66 pytest tests
│   └── requirements.txt
├── frontend/
│   ├── app.py                          Home page
│   ├── api_client.py                   Backend HTTP client
│   ├── pages/                          leads.py, intelligence.py, outreach.py
│   └── requirements.txt
├── data/                               sample_leads.csv, sample_leads_with_issues.csv
├── database/                           init scripts and dumps
├── docs/                               all project documentation
├── pytest.ini
├── run.ps1                             developer command helper
├── SPRINT_PLAN.md
└── README.md
```

**Layering:** `routers → services → models → database`. Route handlers parse and validate the
request; all business rules live in the service layer, which keeps the services testable
without a running server.

---

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/DAY_PLAN.md`](docs/DAY_PLAN.md) | **Day-by-day plan: planned vs completed, with every command** |
| [`docs/SRS.md`](docs/SRS.md) | Software requirements specification |
| [`docs/REQUIREMENTS_CHECKLIST.md`](docs/REQUIREMENTS_CHECKLIST.md) | Every requirement mapped to code and a test |
| [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md) | All 13 endpoints with request/response shapes |
| [`docs/ER_DIAGRAM.md`](docs/ER_DIAGRAM.md) | Tables, columns, keys and relationships |
| [`docs/AGENT_ARCHITECTURE.md`](docs/AGENT_ARCHITECTURE.md) | The intelligence pipeline and the path to a full agent graph |
| [`docs/UI_WIREFRAMES.md`](docs/UI_WIREFRAMES.md) | Screen layouts and behaviour |
| [`docs/TECH_STACK.md`](docs/TECH_STACK.md) | Technology decisions and trade-offs |
| [`docs/TEST_RESULTS.md`](docs/TEST_RESULTS.md) | 66 test cases, 7 bugs found and fixed |
| [`docs/MILESTONE_1_REPORT.md`](docs/MILESTONE_1_REPORT.md) | Milestone 1 report, measured coverage, limitations |
| [`docs/EVALUATION_FEEDBACK.md`](docs/EVALUATION_FEEDBACK.md) | Issue and defect log |
| [`SPRINT_PLAN.md`](SPRINT_PLAN.md) | Sprint backlog |

---

## Testing

```powershell
.\run.ps1 test                          # 66 tests
.\.venv\Scripts\python.exe -m pytest -v # with test names
.\.venv\Scripts\python.exe -m pytest backend/tests/test_lead_import.py -v
```

Expected: `66 passed`.

The suite covers lead CRUD, CSV import and validation, duplicate detection, company analysis,
qualification scoring, outreach generation, performance budgets, migrations, foreign-key
enforcement, and conformance between the implementation and `docs/API_CONTRACTS.md`.

---

## Verification scripts

```powershell
# End-to-end walkthrough against a running backend - prints every step
.\run.ps1 demo

# Measured prospect record coverage (imports, manages and analyses every record)
.\run.ps1 coverage

# Migration state
.\run.ps1 status
```

Latest measured coverage: **100.00 %** over 500 records (threshold: 95 %).

---

## Configuration

All settings come from environment variables; `.env` holds them locally and is git-ignored.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./salesgenie.db` | SQLAlchemy connection URL |
| `API_PREFIX` | `/api` | Prefix for every versioned route |
| `CORS_ORIGINS` | `http://localhost:8501,http://127.0.0.1:8501` | Allowed origins |
| `LLM_API_KEY` | *(empty)* | Provider key. **Empty means mock mode.** |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible endpoint works |
| `LLM_MODEL` | `gpt-4o-mini` | Model identifier |
| `API_BASE_URL` | `http://127.0.0.1:8000` | Backend URL used by the Streamlit client |

See `.env.example` for the full list.

### Using PostgreSQL

```powershell
# In .env:
#   DATABASE_URL=postgresql+psycopg2://salesgenie:<password>@localhost:5432/salesgenie

docker compose up -d db
.\run.ps1 migrate
.\run.ps1 test
```

The migration SQL is portable; the runner expands dialect placeholders for each engine.

---

## AI outreach: mock mode and real mode

With `LLM_API_KEY` empty, the generator produces a deterministic offline draft. **It is always
labelled** — `is_mock: true`, `provider: "mock"` and a note stating it was not produced by an
AI model. The UI shows the same warning. A mock draft is never presented as a real LLM result.

Set `LLM_API_KEY` (and optionally `LLM_BASE_URL` / `LLM_MODEL`) to switch to real generation.
Provider timeouts, HTTP errors and empty responses are handled and surface as a `502` with a
clear message.

Every generated draft is stored with `campaign_status = 'draft'`. Nothing is ever marked `sent`,
because no sending workflow exists in this scope.

---

## Known limitations

| Limitation | Target milestone |
| --- | --- |
| No authentication or role enforcement | Milestone 3 |
| The qualification score is a rule-based heuristic, not a trained model | Milestone 4 |
| Insights come from a static sector reference, not live company research | Milestone 2 |
| No email sending workflow | Milestone 3 |
| No bulk lead operations or CSV export | Milestone 2 |
| The automated suite runs on SQLite; a PostgreSQL CI job is pending | Milestone 2 |

Full list: `docs/MILESTONE_1_REPORT.md` §9.

---

## License

Internal academic project. All sample data is synthetic.
