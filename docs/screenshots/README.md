# Screenshots

Placeholder for the demonstration evidence captured during the Milestone 1 review.

Capture the following at 1440×900 (or larger) and save the PNG files here:

| File | What to show |
| --- | --- |
| `01-home.png` | The home page with the dashboard counters populated |
| `02-leads-list.png` | The Leads page with the imported sample records and the search/filter controls |
| `03-csv-import.png` | The import report after uploading `data/sample_leads_with_issues.csv`, showing the inserted / duplicates / rejected counters and the per-row error table |
| `04-add-lead.png` | The Add Lead form with the validation error state |
| `05-intelligence.png` | The Intelligence page with the company profile, the score and the factor breakdown table |
| `06-intelligence-gaps.png` | The Business needs / Opportunities / Key insights / Information gaps panels |
| `07-outreach.png` | The Outreach page with a generated draft and the mock-mode warning |
| `08-outreach-stored.png` | The stored drafts table |
| `09-swagger.png` | The Swagger UI at `http://127.0.0.1:8000/docs` |
| `10-migration-status.png` | The terminal output of `python backend/scripts/migrate.py --status` |

## How to capture

```powershell
# Terminal 1
python backend\scripts\migrate.py
python -m uvicorn app.main:app --app-dir backend

# Terminal 2
python -m streamlit run frontend\app.py
```

Then open `http://127.0.0.1:8501` and `http://127.0.0.1:8000/docs` and capture the screens above.

Once captured, update `docs/MILESTONE_1_REPORT.md` §10 to link the files, and change the
"Submission evidence" row in `docs/DAY_PLAN.md` from *Partial* to *Complete*.
