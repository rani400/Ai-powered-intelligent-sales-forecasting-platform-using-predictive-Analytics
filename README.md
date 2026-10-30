# SalesGenie AI

**AI-Powered Intelligent Sales Forecasting Platform Using Predictive Analytics**  
**Current scope:** Four-module application | **Frontend:** Streamlit | **Backend:** FastAPI

SalesGenie AI is a sales-lead management and decision-support prototype. It helps users manage prospects, review structured lead intelligence, draft outreach emails, and prioritize follow-ups using transparent scoring and an optional demonstration predictive model.

> **Project scope and accuracy:** The current application implements the four modules documented below. Its lead-intelligence rules use the information entered by users; they do not perform independent company research. The predictive model, when trained, uses **synthetic demonstration data** and is **not a validated real-world sales forecast**.

## Features

| Module | Feature | What it does |
| --- | --- | --- |
| **1** | **Lead Management** | Create, list, search, filter, update, delete, and CSV-import leads; detect duplicates. |
| **2** | **Lead Intelligence** | Summarize submitted lead information; identify possible needs, opportunities, and information gaps; calculate an explainable qualification score. |
| **3** | **AI Outreach** | Generate and save reviewable email **drafts** with selectable tone, goal, and length. Uses an optional configured LLM provider or a local template fallback. **Does not send emails.** |
| **4** | **Lead Scoring & Recommendations** | Calculate a rules-based 0–100 priority score, display its contributing factors, estimate a demonstration conversion probability, and recommend a next action. |

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | Python, Streamlit, Pandas, custom CSS |
| REST API | Python, **FastAPI**, Uvicorn, Pydantic |
| Database | SQLite by default; PostgreSQL supported via SQLAlchemy and Psycopg |
| Data access / migrations | SQLAlchemy 2, Alembic |
| Predictive demonstration | scikit-learn, Pandas, NumPy, Joblib |
| Optional text generation | OpenAI-compatible LLM endpoint configured through environment variables; local template fallback |
| Tests | pytest, FastAPI TestClient, HTTPX |
| Optional containers | Docker, Docker Compose |

**The active backend uses FastAPI, not Flask.** API routes are registered in `app/main.py` and `app/routers/`. The active frontend starts from **`frontend/Home.py`**, not the legacy root-level `frontend.py`.

## Architecture

```text
Streamlit UI (frontend/Home.py + frontend/pages/)
                    |
                    | HTTP / JSON (frontend/components/api.py)
                    v
FastAPI application (app/main.py)
                    |
       +------------+------------+------------+
       |            |            |            |
    /api/leads  /api/intelligence /api/outreach /api/scoring
       |            |            |            |
       +------------+------------+------------+
                    |
       Services / validation / ML helpers
                    |
        SQLAlchemy + Alembic migrations
                    |
           SQLite / PostgreSQL
```

## Project structure

```text
.
├── app/
│   ├── main.py                  # FastAPI entry point and router registration
│   ├── config.py                # Environment settings
│   ├── database.py              # SQLAlchemy engine and DB dependency
│   ├── routers/                 # HTTP routes for Modules 1–4
│   ├── schemas/                 # Pydantic API models
│   ├── services/                # Business logic
│   ├── models/                  # SQLAlchemy entities
│   ├── ml/                      # Training, prediction, evaluation helpers
│   └── utils/
├── frontend/
│   ├── Home.py                  # Current Streamlit entry point
│   ├── pages/                   # Four module pages
│   └── components/              # Shared API client and UI styles
├── migrations/                  # Alembic revisions and configuration
├── data/                        # CSV examples and synthetic training data
├── tests/                       # Automated tests
├── .env.example                 # Example local configuration
├── alembic.ini
├── requirements.txt
├── run_backend.bat
├── run_frontend.bat
├── docker-compose.yml
└── README.md
```

## Local setup (Windows CMD / PowerShell)

### 1. Prerequisites

- Python **3.12** recommended.
- Git is needed only when cloning or contributing changes.
- Optional: PostgreSQL or Docker; **neither is required** for the default SQLite setup.

Open a terminal in the project root (the folder containing `requirements.txt`).

### 2. Create a virtual environment and install packages

```cmd
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `py -3.12` is unavailable, install Python 3.12 or use an existing compatible Python installation with `py -m venv .venv`.

### 3. Configure environment (optional for local SQLite)

```cmd
copy .env.example .env
```

By default, the application uses a local SQLite database at **`salesgenie.db` in the project root**. To connect PostgreSQL instead, set `DATABASE_URL` in your uncommitted `.env` file.

For local operation, you can leave `LLM_PROVIDER=mock` and `LLM_API_KEY` empty; email drafts will use the local template. Do not commit `.env`, secrets, or real customer information.

### 4. Initialize or migrate the database

**Run migrations before starting the backend:**

```cmd
.venv\Scripts\python.exe -m alembic upgrade head
```

The default SQLite database file is created when migrations run against the configured database.

### 5. Start the FastAPI backend

In the first terminal:

```cmd
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- Health check: <http://127.0.0.1:8000/health>
- Interactive Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI specification: <http://127.0.0.1:8000/openapi.json>

The health endpoint reports `active_modules: 4` when this four-module app is running.

### 6. Start the **correct** Streamlit frontend

In a **second terminal**, from the same project root:

```cmd
.venv\Scripts\python.exe -m streamlit run frontend/Home.py
```

Open <http://localhost:8501>. Alternatively, use `run_frontend.bat` after installing dependencies and applying migrations. Keep the backend running in its own terminal.

**Do not run `streamlit run frontend.py`.** The root-level `frontend.py` is a legacy entry point with incompatible API paths and response formats.

## API reference

All four module APIs are available from the FastAPI Swagger interface at `/docs`.

### Module 1 — Lead Management

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/leads` | List, search, filter, and paginate leads |
| `POST` | `/api/leads` | Create a lead |
| `POST` | `/api/leads/import` | Import CSV leads (`multipart/form-data`) |
| `GET` | `/api/leads/{lead_id}` | Retrieve a lead |
| `PATCH` | `/api/leads/{lead_id}` | Update fields on a lead |
| `DELETE` | `/api/leads/{lead_id}` | Delete a lead |

`GET /api/leads` returns a paginated object with `total`, `page`, `page_size`, and `items`. Lead identifiers use the field name **`lead_id`**, not `id`.

Example JSON for `POST /api/leads`:

```json
{
  "company_name": "Northstar Retail",
  "industry": "Retail",
  "contact_name": "Asha Menon",
  "email": "asha@example.com",
  "phone": "555-0101",
  "company_size": "51-200",
  "lead_status": "New",
  "engagement_score": 65,
  "source": "Website",
  "notes": "Interested in a discovery call"
}
```

Allowed `lead_status` values: `New`, `Contacted`, `Qualified`, `Converted`. Engagement score must be between 0 and 100. `company_name` is required.

For CSV imports, use supported headers such as:

```csv
company_name,industry,contact_name,email,phone,lead_status,company_size,engagement_score,source
Northstar Retail,Retail,Asha Menon,asha@example.com,555-0101,New,51-200,65,Website
```

CSV imports support `duplicate_policy=reject`, `skip`, or `update_existing`. Import processing reports inserted, rejected, duplicate, updated, and skipped rows. **Note:** Some older CSV example/template files may contain fields that the current lead schema no longer accepts; the header above matches the current implementation.

### Module 2 — Lead Intelligence

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/intelligence/{lead_id}/analyze` | Create and save an analysis for a lead |
| `GET` | `/api/intelligence/{lead_id}` | Retrieve the latest saved analysis |

Results include a company summary, general industry context, potential needs and opportunities, observations, information gaps, and rule-based qualification factors. Company facts are **not independently verified**.

### Module 3 — AI Outreach

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/outreach/generate` | Generate and save an email draft |
| `GET` | `/api/outreach/leads/{lead_id}/drafts` | View saved draft history for a lead |

Example JSON for `POST /api/outreach/generate`:

```json
{
  "lead_id": 1,
  "tone": "Professional",
  "communication_goal": "Discovery call",
  "email_length": "Medium"
}
```

Supported tones: `Professional`, `Friendly`, `Concise`, `Persuasive`; goals: `Introduction`, `Discovery call`, `Follow-up`, `Meeting request`, `Re-engagement`; lengths: `Short`, `Medium`, `Long`.

The application **creates drafts only**. An optional configured LLM provider can generate the content; the system falls back to a local template when a provider is not configured or is unavailable. No emails are automatically sent.

### Module 4 — Lead Scoring & Recommendations

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/scoring/{lead_id}/score` | Compute and save a lead score and recommendation |
| `GET` | `/api/scoring/{lead_id}` | Retrieve the latest saved score |
| `GET` | `/api/scoring/model/status` | Check whether the demo model and its metrics are available |

The module distinguishes its **explainable rules-based priority score** from its **demonstration conversion estimate**. If a trained synthetic-demo model is unavailable, prediction uses a labeled heuristic fallback. For a lead already marked `Converted`, the displayed 100% reflects its recorded status rather than a forecast.

### System endpoint

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Basic application health and active module count |

## Optional: train the demonstration ML model

A reproducible logistic-regression demonstration can be trained from the repository's **synthetic** sample dataset:

```cmd
.venv\Scripts\python.exe -m app.ml.train
```

This generates model and metrics files under `artifacts/` by default. The application reads these through `MODEL_PATH` and `METRICS_PATH` settings when configured, or their default paths. **Do not present synthetic-data evaluation metrics as real sales forecasting accuracy.** Without a trained artifact, the API uses its clearly identified heuristic mode.

## Optional: Docker Compose

Docker Compose provides PostgreSQL, the FastAPI backend, and the Streamlit frontend. Set `POSTGRES_PASSWORD` to a private value in `.env` first, then run:

```cmd
docker compose up --build
```

The frontend and backend are exposed on local ports `8501` and `8000` respectively. The frontend container connects to the backend service via `SALES_API_URL`.

## Testing

Run the test suite from the project root:

```cmd
.venv\Scripts\python.exe -m pytest -q
```

For manual testing, first create a prospect from the Lead Management page, then analyze it, generate an outreach draft, and calculate its score. Check `/docs` for request validation and response bodies.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `404 Not Found` for `/leads` | The current URL is **`/api/leads`**. Launch `frontend/Home.py`, not the old `frontend.py`. |
| Frontend says backend is unavailable | Start Uvicorn in a separate terminal; check <http://127.0.0.1:8000/health>. |
| Database tables are missing | Run `python -m alembic upgrade head` with the virtual environment's Python. |
| `404` for a lead's analysis or score | Create the analysis or score first; the corresponding `GET` returns the latest saved result. |
| Outreach uses a local template | This is expected with `LLM_PROVIDER=mock`, missing credentials, or an unavailable LLM provider. |
| Missing or incompatible Python packages | Use the project's `requirements.txt` and a compatible Python version (3.12 recommended). |

## Contributing and security

- Work on feature branches, test changes locally, and open a pull request for review before merging into `main`.
- Keep the frontend and backend API contract consistent; use the paths documented above.
- Never commit `.env`, tokens, passwords, local databases, model artifacts, or personal customer information.
- Review generated outreach drafts before external use.

---

**SalesGenie AI — Four-module FastAPI + Streamlit prototype.**
