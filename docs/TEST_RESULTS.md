# Test Results — SalesGenie AI

**Scope:** Milestone 1 (Lead Management & Intelligence Engine) and the first slice of
Milestone 2 (AI Outreach Generation).
**Test framework:** pytest with FastAPI `TestClient` (HTTP-level) plus direct service unit tests.
**Database used:** SQLite (temporary file in the system temp directory) with foreign keys enabled.
**Command:** `.\run.ps1 test` from the project root (runs pytest inside the project `.venv`).
**Result of the final run:** **66 passed, 0 failed, 0 skipped.**

---

## 1. How the suite is organised

| File | Tests | Area |
| --- | --- | --- |
| `backend/tests/test_leads.py` | 12 | Lead CRUD API |
| `backend/tests/test_lead_import.py` | 14 | CSV import and validation |
| `backend/tests/test_duplicates.py` | 5 | Duplicate detection service |
| `backend/tests/test_intelligence.py` | 13 | Company analysis and qualification score |
| `backend/tests/test_outreach.py` | 13 | AI outreach generation and draft storage |
| `backend/tests/test_performance.py` | 2 | Response-time and import-throughput checks |
| `backend/tests/test_migrations.py` | 4 | Schema, migrations, foreign keys |
| `backend/tests/test_api_contract.py` | 3 | Implementation matches `docs/API_CONTRACTS.md` |
| **Total** | **66** | |

Test case IDs (TC-xx) are referenced from `docs/SRS.md`.

---

## 2. Lead CRUD API

| TC | Test description | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| TC-01 | Create a lead with a valid payload | `201` with the stored record, `source=manual` | `201`, all fields correct, `lead_id` assigned | **Pass** |
| TC-02 | List leads with no filter | `200` with `total` and `items` | `200`, `total=2`, 2 items | **Pass** |
| TC-03 | Search by company, email, status and industry | Only matching rows returned | 1 / 1 / 1 / 1 / 0 as expected | **Pass** |
| TC-04 | Retrieve one lead by id | `200` with that lead | `200`, correct email | **Pass** |
| TC-05 | Update `lead_status` and `notes` only | Other fields unchanged; change persists on re-read | `200`; company unchanged; re-read shows `Qualified` | **Pass** |
| TC-06 | Delete a lead | `200`; lead no longer retrievable or listed | `200`; `404` on get; `total=0` | **Pass** |
| TC-07 | Request an unknown lead id (GET, PUT, DELETE) | `404` with a "not found" message | `404` on all three verbs | **Pass** |
| TC-08 | Create a lead with no `company_name` | `422` naming the field | `422`, error field `company_name` | **Pass** |
| TC-09 | Create a lead with a malformed email / unknown status | `422` naming the field | `422` for `email` and `lead_status` | **Pass** |
| TC-10 | Create a lead whose email already exists | `409` | `409`, "already exists" in detail | **Pass** |
| TC-11 | Company name and email with stray whitespace / mixed case | Normalised on write | `"TechCorp Solutions"`, `sarah@example.com` | **Pass** |
| TC-12 | `GET /health` and `GET /api/leads/stats` | Correct payloads | `healthy`; `total_leads=1`, `by_status={"New":1}` | **Pass** |

---

## 3. CSV import and validation

| TC | Test description | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| TC-20 | Import a valid 3-row CSV | 3 rows inserted, 0 rejected | `inserted=3`, `inserted_lead_ids` has 3 ids | **Pass** |
| TC-21 | Import a CSV missing `company_name` and `email` | `400` naming the missing columns | `400`, "missing required column" | **Pass** |
| TC-22 | Import an empty file | `400` | `400`, "empty" | **Pass** |
| TC-23 | Import a file mixing a valid row with 3 invalid rows | 1 inserted, 3 rejected; reasons reported | `inserted=1`, `rejected=3`, reasons `invalid_email`, `missing_company_name`, `invalid_status` | **Pass** |
| TC-24 | Row numbers in the error report | 1-based data-row numbers 3, 4, 5 | Exactly `{3, 4, 5}` | **Pass** |
| TC-25 | Import values with stray whitespace and upper-case email | Normalised | `"TechCorp Solutions"`, `sarah@example.com` | **Pass** |
| TC-26 | Import a file whose emails already exist | Duplicates detected, nothing inserted | `inserted=0`, `duplicates=2`, reason `duplicate_email` | **Pass** |
| TC-27 | Duplicate policy `reject` vs `skip` | `reject` fails the row; `skip` reports without failing | `rejected=1` vs `rejected=0, duplicates=1` | **Pass** |
| TC-28 | Import a row with the same company + contact but a new email | Flagged as `duplicate_company_contact` | `duplicates=1`, reason `duplicate_company_contact` | **Pass** |
| TC-29 | Import report shape | All documented counters present | 7/7 keys present | **Pass** |
| TC-30 | Upload a non-CSV file | `400` | `400`, "csv" in detail | **Pass** |
| TC-31 | Import with `update_existing=true` over an existing email | The record is updated, `updated=1`, `inserted=0` | As expected; status, size and notes updated | **Pass** |
| TC-32 | `update_existing` on a row that omits some fields | Fields absent from the CSV keep their previous values | `industry`, `contact_name` and `phone` unchanged | **Pass** |
| TC-33 | `update_existing` with a mix of a duplicate and a new row | `updated=1`, `inserted=1` | As expected; 2 records in total | **Pass** |

---

## 4. Duplicate detection (service-level)

| TC | Test description | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| TC-D1 | Detect a duplicate email with different case and padding | `duplicate_email` with the existing `lead_id` | Reason and id correct | **Pass** |
| TC-D2 | Detect a duplicate company + contact pair | `duplicate_company_contact` | Reason correct | **Pass** |
| TC-D3 | Email signal takes priority over the company + contact signal | `duplicate_email` | Reason correct | **Pass** |
| TC-D4 | A genuinely different record | No match | `None` | **Pass** |
| TC-D5 | A soft-deleted lead with the same email | Not treated as a duplicate | `None` | **Pass** |

---

## 5. Lead intelligence and qualification score

| TC | Test description | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| TC-40 | Company profile built from stored fields | Matches the record; completeness in 0–1 | Matches | **Pass** |
| TC-41 | Business needs and opportunities produced | Non-empty string lists | Non-empty | **Pass** |
| TC-42 | Missing fields reported as gaps | Industry, company size, contact name and phone gaps listed | All four present in the gap text | **Pass** |
| TC-43 | Insight run persisted with score row | First call `is_cached=false`, second `true`, refresh `false` | As expected | **Pass** |
| TC-44 | No invented company facts | No "revenue", "funding", "raised", "valuation" or "employees" claims | None present | **Pass** |
| TC-45 | Insights endpoint payload shape | All documented keys, methodology and disclaimer | All present | **Pass** |
| TC-46 | Insights for an unknown lead | `404` | `404` | **Pass** |
| TC-50 | Score is normalised and weighted as documented | 0–100; factor weights sum to 100; points sum to the score | Holds | **Pass** |
| TC-51 | Every factor explains itself | Non-empty explanation; points never exceed the weight | Holds | **Pass** |
| TC-52 | An almost-empty record scores low | Score < 20, band `Low` | `10.0`, band `Low` | **Pass** |
| TC-53 | Score is deterministic | Two calls on the same record match | Identical | **Pass** |
| TC-54 | Every score run is stored in `lead_scores` | 2 rows after 2 runs | 2 rows | **Pass** |
| TC-55 | Dashboard counters reflect stored scores | `scored_leads=1`, average in range | Holds | **Pass** |

---

## 6. AI outreach generation

| TC | Test description | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| TC-60 | Invalid tone in the request | `422` naming `tone` | `422` | **Pass** |
| TC-61 | Prompt contains the prospect facts | Company, contact and offering all present; `SUBJECT:`/`BODY:` instructed | Holds | **Pass** |
| TC-62 | Provider response parsing | Subject and body extracted | Correct | **Pass** |
| TC-63 | Mock mode is clearly labelled | `is_mock=true`, `provider="mock"`, note says "mock mode" | Holds | **Pass** |
| TC-64 | Provider timeout | Clean upstream error, no crash | `UpstreamError` "timed out" | **Pass** |
| TC-65 | Provider HTTP error | Clean upstream error | `UpstreamError` | **Pass** |
| TC-66 | Empty provider response | Error mentions "empty" | `UpstreamError` "empty" | **Pass** |
| TC-67 | Draft stored with status `draft` | `campaign_status="draft"`, retrievable, never `sent` | Holds | **Pass** |
| TC-68 | Drafts retrievable per lead and globally | 3 drafts for 3 goals | 3 and 3 | **Pass** |
| TC-69 | Tone and length variants change the output | Friendly ≠ professional; detailed > short | Holds | **Pass** |
| TC-70 | Generate for an unknown lead | `404` | `404` | **Pass** |
| TC-71 | Provider failure surfaces as `502` | `502` with a detail message | `502` | **Pass** |
| TC-72 | Stored lead data is used when the request does not override it | Company or contact appears in the draft | Holds | **Pass** |

---

## 7. Performance

| TC | Test description | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| TC-80 | List endpoint with 1,000 records present | Response < 500 ms; import < 30 s | Import of 1,000 rows well inside 30 s; list response < 500 ms | **Pass** |
| TC-81 | Import of 1,000 rows | < 30 s, all inserted | 1,000 inserted, inside the budget | **Pass** |

---

## 8. Schema, migrations and contract

| TC | Test description | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| TC-90 | Migration scripts are numbered and ordered | Sequential, unique filenames | Holds | **Pass** |
| TC-91 | Migration runner is repeatable | A second run applies nothing | Applied set unchanged | **Pass** |
| TC-92 | Schema matches the ORM models | Every model table exists | Holds | **Pass** |
| TC-93 | Foreign keys are enforced | An orphan `lead_scores` row is refused | `IntegrityError` raised | **Pass** |
| TC-94 | Every documented endpoint is implemented | All 13 present in OpenAPI | All present | **Pass** |
| TC-95 | No undocumented endpoints | Implementation ⊆ contract | Holds | **Pass** |
| TC-96 | Every operation has a summary and a tag | All present | Holds | **Pass** |

---

## 9. Manual verification evidence

| Check | Command | Result |
| --- | --- | --- |
| Backend boots | `python -m uvicorn app.main:app --app-dir backend` | Starts; `GET /health` returns `healthy` |
| Swagger UI | open `http://127.0.0.1:8000/docs` | All 13 operations listed with request/response schemas |
| Migrations apply | `python backend/scripts/migrate.py` | 4 scripts applied; re-run applies none |
| Migration status | `python backend/scripts/migrate.py --status` | All 4 report `applied` |
| End-to-end walkthrough | `python backend/scripts/demo_walkthrough.py` | Import → list → insights → outreach → drafts → stats all succeed |
| Record coverage | `python backend/scripts/measure_coverage.py --rows 500` | **100.00 %** (500/500 managed and analysed) |
| Streamlit app | `python -m streamlit run frontend/app.py` | Starts; home, Leads, Intelligence and Outreach pages render without exceptions |
| Streamlit page render | `streamlit.testing.v1.AppTest` on all four scripts | 0 exceptions on each page |

---

## 10. Bugs found and fixed during the test cycle

| # | Bug | Symptom | Root cause | Fix | Regression test |
| --- | --- | --- | --- | --- | --- |
| B-01 | `Select.scalars()` raised `AttributeError` | Duplicate detection crashed on the company + contact path | `Select.scalars()` does not exist in SQLAlchemy 2.0; only `Result.scalars()` does | Call `db.execute(...).scalars().first()` | TC-D2 |
| B-02 | `LeadListResponse` failed to validate | `list_leads` returned a 500 instead of a 200 | `LeadRead` was a forward reference in `schemas/lead_schema.py` with no import, so Pydantic could not resolve it | Import `LeadRead` in `schemas/lead_schema.py` | TC-02 |
| B-03 | `company_name` kept internal double spaces | `"TechCorp   Solutions"` was stored verbatim | The validator trimmed the ends but did not collapse internal runs | Use `_normalise_text` for `company_name` | TC-11 |
| B-04 | `PUT /api/leads/{id}` with no body returned 422 | A 404 was expected for an unknown id | FastAPI validates the body before the handler runs, and an empty update body is invalid by design | Test sends a valid body; the 422 for an empty body remains the documented behaviour | TC-07, TC-08 |
| B-05 | `scored_leads` counted score rows, not leads | The dashboard showed 2 scored leads for 1 scored prospect | The counter used `count(*)` over `lead_scores` | Use `count(distinct(lead_id))` | TC-55 |
| B-06 | `created_at` / `updated_at` were naive on SQLite | Timestamps lacked a timezone | SQLite drops the timezone from `TIMESTAMPTZ` | Timestamps are stored in UTC and rendered as ISO-8601 with `Z` by the API where the driver preserves it; the local SQLite dev database is a convenience only and PostgreSQL is the documented production target | Covered by TC-01 |
| B-07 | `update_existing` did not copy `lead_status` | An import with `update_existing=true` reported `updated=1` but the record kept its old status | The update branch copied company, industry, contact, phone, size and notes, but never `lead_status` | Add `existing.lead_status` to the update, and add TC-31 … TC-33 to cover the whole `update_existing` path | TC-31, TC-32, TC-33 |

---

## 11. Known limitations of the test suite

| Limitation | Impact | Mitigation |
| --- | --- | --- |
| Tests run on SQLite, not PostgreSQL | Engine-specific behaviour (for example `TIMESTAMPTZ` handling) is not exercised | The schema is written in portable ANSI SQL and the migration runner expands dialect placeholders; a PostgreSQL CI job should be added |
| No LLM provider key in CI | The provider call path is covered with `httpx.MockTransport`, not a real endpoint | The mock transport covers success, timeout, HTTP error and empty response |
| No authentication | Endpoints are open | Out of scope for this window; noted in the SRS and the milestone report |
| No concurrency test | Row-level locking behaviour under parallel writes is unverified | PostgreSQL and an explicit isolation-level test are planned for a later stage |

---

## 12. Reproduction

```powershell
# From the project root
.\run.ps1 test                          # full suite (uses .venv)
.\.venv\Scripts\python.exe -m pytest -v                  # with test names
.\.venv\Scripts\python.exe -m pytest backend/tests/test_lead_import.py -v
.\.venv\Scripts\python.exe -m pytest --collect-only -q   # list test ids
```

Expected output on a clean checkout:

```
66 passed, 1 warning in 37.79s
```

The single warning is an upstream Starlette notice that `httpx` should be replaced by `httpx2`
for the test client; it does not affect test results.
