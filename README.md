# SalesGenie AI — Complete Four-Module Project

This project implements **only** the four modules requested in the team slide:

1. **Lead Management** — create, search, view, update, and delete prospect records in SQLite.
2. **Lead Intelligence** — infer potential business needs and opportunities from supplied company/lead fields.
3. **AI Outreach** — create personalised email drafts in professional, friendly, or concise tone. Drafts are not sent.
4. **Lead Scoring** — transparent 0–100 rule-based qualification score, factors, and recommended next action.

Conversation Intelligence and Analytics Dashboard are intentionally not implemented.

## Technology
- Python 3.10+
- Streamlit frontend
- FastAPI backend
- SQLite database (no separate database installation required)
- Pydantic request validation

## Run on Windows PowerShell
Open a terminal in this project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Keep that terminal open. Open a **second terminal** in the same project folder and run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend.py
```

Open the Streamlit URL printed in the terminal, normally `http://localhost:8501`. API documentation is at `http://127.0.0.1:8000/docs`.

You can also double-click `run_backend.bat` and `run_frontend.bat` in that order. The first run installs dependencies and may require internet access. If you have an existing Python environment, install `requirements.txt` there instead.

## Modules and API endpoints
### Module 1 — Lead Management
- `POST /leads` — create a lead
- `GET /leads` — list/search/filter leads
- `GET /leads/{lead_id}` — get one lead
- `PATCH /leads/{lead_id}` — update a lead
- `DELETE /leads/{lead_id}` — delete a lead

### Module 2 — Lead Intelligence
- `GET /leads/{lead_id}/company-analysis` — company summary, potential needs, opportunities
- `GET /leads/{lead_id}/intelligence` — company analysis plus lead score

### Module 3 — AI Outreach
- `POST /leads/{lead_id}/outreach` — create a personalised email draft

Example request:
```json
{"tone":"professional","goal":"schedule a 15-minute discovery call"}
```

### Module 4 — Lead Scoring
- `GET /leads/{lead_id}/score` — score, factors, tier, recommendation

## Database and sample data
The SQLite database is created automatically at `data/salesgenie.db` on first startup. `data/sample_leads.csv` is example data for development; it is not automatically imported. Add leads through the Streamlit Lead Management page, the API docs, or the CSV importer in Lead Management. The CSV importer includes a downloadable `data/lead_import_template.csv`; `company_name` is required and the other columns are optional. Rows are validated by the API, and any row errors are displayed after import; successful rows are saved even if another row fails.

## Important accuracy notes
- The lead score is an **explainable rule-based baseline**, not a trained machine-learning model and not a true conversion probability.
- To train a predictive model, the team must supply historical leads with known conversion outcomes, then evaluate it on held-out data.
- Company insights are inferred from user-supplied fields and broad industry hints; they are not independently verified company research.
- Outreach creates drafts only and does not send emails. This version does not call a paid LLM API; the draft generator is template-based. Add an approved LLM provider only after your team agrees on which provider to use and supplies an API key securely.
- The project implements the four current modules; Conversation Intelligence and Analytics Dashboard remain future work.
- Do not commit API keys, credentials, or real customer data to GitHub.

## Project structure
```text
salesgenie_four_modules/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── schemas.py
│   └── services.py
├── data/
│   ├── lead_import_template.csv
│   ├── lead_import_test.csv
│   └── sample_leads.csv
├── frontend.py
├── requirements.txt
├── .env.example
├── run_backend.bat
├── run_frontend.bat
└── README.md
```
