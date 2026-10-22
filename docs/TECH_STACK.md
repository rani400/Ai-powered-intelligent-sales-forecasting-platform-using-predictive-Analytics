# Technology Stack — SalesGenie AI

**Decision record for the 12–21 October 2026 window.** Each choice lists the reason, the
alternatives that were rejected, and the trade-off that was accepted.

---

## 1. Stack summary

| Layer | Choice | Version | Role |
| --- | --- | --- | --- |
| Language | Python | 3.11+ (3.13 used in development) | Backend, services and tests |
| Web framework | FastAPI | 0.115 | REST API, OpenAPI docs, dependency injection |
| ASGI server | Uvicorn | 0.34 | Serves the API |
| Validation | Pydantic | 2.10 | Request/response schemas, field validators |
| Settings | pydantic-settings + python-dotenv | 2.7 / 1.0 | Environment-driven configuration |
| ORM | SQLAlchemy | 2.0 | Typed declarative models, sessions |
| Database | PostgreSQL | 14+ | Production store |
| Development database | SQLite | 3.35+ | Local development and automated tests |
| Migrations | Versioned SQL + a custom runner | — | Repeatable, reviewable schema changes |
| Data processing | Pandas | 2.2 | CSV handling, reporting tables |
| Machine learning | Scikit-learn | 1.6 | Available for the later learned scoring model |
| Frontend | Streamlit | 1.51 | Operator interface, no build step |
| AI provider | Any OpenAI-compatible chat-completions API | — | Outreach generation |
| HTTP client | httpx + requests | 0.28 / 2.32 | Backend calls from the frontend and from services |
| Testing | pytest + FastAPI TestClient | 8.3 | Automated test suite |

---

## 2. Decisions and rationale

### 2.1 FastAPI over Flask / Django

**Why:** automatic OpenAPI generation (the API contract is generated from the code, so it cannot
drift), request validation built in through Pydantic, and native async support.

**Rejected:** Flask (no schema layer, so validation would be hand-written), Django REST Framework
(a full ORM and admin would duplicate what SQLAlchemy and Streamlit already cover).

**Accepted trade-off:** the dependency stack is heavier than Flask.

### 2.2 Pydantic v2 for both API and service validation

The same validators normalise and validate a payload whether it arrives from HTTP or from a CSV
row, so a record created by import and one created by the API are identical in shape. Validation
lives in `schemas/lead_schema.py`, not in the route handlers.

### 2.3 SQLAlchemy 2.0 with typed declarative models

**Why:** typed `Mapped[...]` columns give static clarity, and the ORM maps cleanly onto both
PostgreSQL and SQLite.

**Rejected:** raw SQL (no relationship management, more injection surface), SQLModel (adds a
second schema layer on top of Pydantic for little gain here).

### 2.4 PostgreSQL as the production target, SQLite for development and tests

**Why:** PostgreSQL is what the SDLC schedule specifies and it enforces foreign keys natively.
SQLite keeps the repository runnable and the test suite fast with no server to install.

**How the switch works:** one environment variable. `DATABASE_URL` selects the engine; the
migration runner expands dialect placeholders (`{{PK}}`, `{{FK_TYPE}}`, `{{TS}}`) for the target.

**Accepted trade-off:** the automated suite currently runs on SQLite, so PostgreSQL-specific
behaviour (notably timezone handling) is not exercised. A PostgreSQL CI job is on the backlog.

### 2.5 A custom migration runner over Alembic

**Why:** the migration scripts are plain SQL, which makes them reviewable in a pull request and
portable across both engines. The runner tracks applied versions in `schema_migrations`, so a
script is never applied twice.

**Rejected:** Alembic (its autogen workflow was not needed; the schema is small and stable, and
the environment had no network access to install the package).

**Accepted trade-off:** no automatic model-to-migration generation, so schema changes need a
hand-written script.

### 2.6 Streamlit over React / Vue

**Why:** the deliverable is an internal operator tool, not a customer-facing product. Streamlit
delivers a working interface with no build chain, no node_modules and no separate deployment
target, which matters for a 10-day sprint.

**Rejected:** React + a REST client (two extra toolchains for no user-visible benefit), Flask
templates (would duplicate the API's validation).

**Accepted trade-off:** less control over the rendered UI and a weaker story for a public-facing
product. If the tool becomes customer-facing, the API already exposes everything the UI needs,
so only the frontend would be replaced.

### 2.7 A provider-agnostic LLM client with a labelled mock fallback

**Why:** any OpenAI-compatible chat-completions endpoint works, so the platform is not locked to
one vendor. When no key is configured the service returns a deterministic offline draft that is
**always** labelled `is_mock=true` with a note explaining why.

**Accepted trade-off:** the mock path is not AI output. It is never presented as such — the API
response, the database row, the UI and the documentation all state the difference.

### 2.8 A rule-based qualification score rather than a trained model

**Why:** there is no labelled outcome history yet, so a trained model would be fitting noise. A
transparent weighted heuristic is honest about what it measures and can be explained to a sales
manager factor by factor.

**Rejected:** a scikit-learn model trained on synthetic labels (it would look sophisticated and
be meaningless).

**Accepted trade-off:** the score ranks records by data completeness and configured fit, not by
likelihood of purchase. The API payload, the UI and the documentation all state this.

### 2.9 Pandas for CSV and reporting only

**Why:** it handles quoting, ragged rows and type inference robustly, and it powers the tables in
the Streamlit interface.

**Accepted trade-off:** a heavyweight dependency for what is ultimately a small amount of CSV
parsing. The import service uses the standard-library `csv` module for correctness-critical
parsing and keeps Pandas for reporting.

---

## 3. Project structure

```
salesgenie-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 FastAPI application entry point
│   │   ├── config.py               Environment-driven settings
│   │   ├── database.py             Engine, session factory, Base
│   │   ├── errors.py               Domain errors and the error envelope
│   │   ├── models/                 SQLAlchemy ORM models
│   │   ├── schemas/                Pydantic request/response models
│   │   ├── routers/                HTTP routes (thin)
│   │   ├── services/               Business logic
│   │   └── utils/                  Shared normalisation helpers
│   ├── migrations/                 Versioned SQL scripts
│   ├── scripts/                    migrate.py, demo_walkthrough.py, measure_coverage.py
│   ├── tests/                      pytest suite
│   └── requirements.txt
├── frontend/
│   ├── app.py                      Home page
│   ├── api_client.py               HTTP client for the backend
│   └── pages/                      leads.py, intelligence.py, outreach.py
├── data/                           Sample datasets
├── database/                       Reserved for database artefacts
├── docs/                           All project documentation
├── pytest.ini                      Test configuration
├── SPRINT_PLAN.md                  Sprint backlog
└── README.md
```

**Exact module layout**

| Path | Responsibility |
| --- | --- |
| `app/main.py` | Application factory, middleware, router registration, lifespan |
| `app/config.py` | Environment-driven settings singleton |
| `app/database.py` | Engine, session factory, declarative base |
| `app/errors.py` | Domain exceptions and the shared error envelope |
| `app/models/lead.py` | `leads` table |
| `app/models/lead_score.py` | `lead_scores` table |
| `app/models/company_insight.py` | `company_insights` table |
| `app/models/outreach_campaign.py` | `outreach_campaigns` table |
| `app/models/extended.py` | Tables reserved for the later milestones (schema only) |
| `app/schemas/lead_schema.py` | Lead CRUD, import report, intelligence and shared response schemas |
| `app/schemas/outreach_schema.py` | Outreach request and response schemas |
| `app/routers/leads.py` | Lead CRUD, CSV import and counters |
| `app/routers/company_analysis.py` | Lead intelligence and qualification score endpoints |
| `app/routers/outreach.py` | Outreach generation, campaign listing and per-lead drafts |
| `app/services/lead_service.py` | Lead CRUD business rules |
| `app/services/lead_import.py` | CSV parsing, row validation and import reporting |
| `app/services/duplicate_detection.py` | Duplicate detection rules |
| `app/services/lead_intelligence.py` | Company analysis, sector reference and qualification scoring |
| `app/services/outreach_generator.py` | Prompt templates, provider client and the labelled mock generator |
| `app/utils/validation.py` | Shared normalisation helpers |
| `backend/tests/test_leads.py` | Lead CRUD API tests |
| `backend/tests/test_lead_import.py` | CSV import and validation tests |
| `backend/tests/test_duplicates.py` | Duplicate detection tests |
| `backend/tests/test_intelligence.py` | Intelligence and scoring tests |
| `backend/tests/test_outreach.py` | Outreach generation tests |
| `backend/tests/test_performance.py` | Response-time and import-throughput tests |
| `backend/tests/test_migrations.py` | Schema, migration and foreign-key tests |
| `backend/tests/test_api_contract.py` | Contract-versus-implementation tests |

**Layering rule:** `routers → services → models → database`. Route handlers parse and validate
the request and nothing else; all business rules live in the service layer. This is what makes
the services unit-testable without a running server (NFR-15).

---

## 4. Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./salesgenie.db` | SQLAlchemy connection URL |
| `SQLITE_FOREIGN_KEYS` | `true` | Enables `PRAGMA foreign_keys=ON` |
| `APP_NAME` | `SalesGenie AI` | Application name |
| `APP_VERSION` | `1.0.0` | Version reported by `/health` |
| `API_PREFIX` | `/api` | Prefix for every versioned route |
| `DEBUG` | `false` | Verbose logging |
| `CORS_ORIGINS` | `http://localhost:8501,http://127.0.0.1:8501` | Allowed origins |
| `LLM_API_KEY` | *(empty)* | Provider key; empty enables mock mode |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Provider base URL |
| `LLM_MODEL` | `gpt-4o-mini` | Model identifier |
| `LLM_TIMEOUT_SECONDS` | `30` | Provider timeout |
| `LLM_MAX_RETRIES` | `2` | Provider retries |
| `API_BASE_URL` | `http://127.0.0.1:8000` | Backend URL used by the Streamlit client |

---

## 5. Version pinning

`backend/requirements.txt` pins exact versions so a build is reproducible. The versions recorded
there match the ones used for the verification runs in `docs/TEST_RESULTS.md`.

---

## 6. Deferred technology decisions

| Decision | Deferred to | Reason |
| --- | --- | --- |
| Container orchestration | Post-window | `docker-compose.yml` is provided for local use only |
| CI/CD pipeline | Milestone 2+ | No hosting target selected |
| PostgreSQL in CI | Milestone 2+ | The suite currently runs on SQLite |
| Authentication provider | Milestone 3+ | No identity system selected |
| Vector store for company research | Milestone 2 | Depends on the chosen research data source |
