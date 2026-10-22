# Milestone 1 Report — Lead Management & Intelligence Engine

**Project:** SalesGenie AI — AI Sales Assistant & Lead Intelligence Platform
**Milestone:** 1 — Lead Management & Intelligence Engine
**Window:** 12 October 2026 – 21 October 2026
**Report status:** Complete and ready for review (formal approval is the evaluator's decision)
**Test result:** 66 automated tests — 66 passed, 0 failed

---

## 1. Features implemented

| # | Feature | Status | Where |
| --- | --- | --- | --- |
| 1 | Prospect database with full CRUD | **Implemented** | `routers/leads.py`, `services/lead_service.py` |
| 2 | Field validation (required fields, email format, status enum, phone format) | **Implemented** | `schemas/lead_schema.py` |
| 3 | Value normalisation (trim, collapse whitespace, lower-case email) on every write path | **Implemented** | `schemas/lead_schema.py`, `utils/validation.py` |
| 4 | CSV import with per-row validation and a full import report | **Implemented** | `services/lead_import.py` |
| 5 | Duplicate detection (email hard match, company + contact soft match) | **Implemented** | `services/duplicate_detection.py` |
| 6 | Company insights, needs, opportunities, key insights and information gaps | **Implemented** | `services/lead_intelligence.py` |
| 7 | Transparent 0–100 qualification score with a factor breakdown | **Implemented** | `services/lead_intelligence.py` |
| 8 | Persisted insight and score history (`company_insights`, `lead_scores`) | **Implemented** | `models/company_insight.py`, `models/lead_score.py` |
| 9 | Streamlit interface: Leads, Intelligence and Outreach pages | **Implemented** | `frontend/` |
| 10 | Versioned database migrations with a repeatable runner | **Implemented** | `backend/migrations/`, `backend/scripts/migrate.py` |
| 11 | Consistent JSON error envelope and HTTP status handling | **Implemented** | `app/errors.py` |
| 12 | AI outreach generation (first slice of Milestone 2) with prompt templates | **Implemented** | `services/outreach_generator.py`, `services/outreach_generator.py` |
| 13 | Outreach draft storage (`outreach_campaigns`) | **Implemented** | `models/outreach_campaign.py` |
| 14 | Schema for the later modules (users, interactions, CRM logs, analytics) | **Designed, no logic** | `models/extended.py`, `migrations/004_*` |
| 15 | Learned conversion-probability model | **Not implemented** — out of scope | — |
| 16 | CRM integration | **Not implemented** — out of scope | — |
| 17 | Conversation intelligence | **Not implemented** — out of scope | — |
| 18 | Full sales analytics dashboard | **Not implemented** — out of scope | `GET /api/leads/stats` is a counter endpoint only |
| 19 | Email sending workflow | **Not implemented** — out of scope; drafts stay `draft` | — |
| 20 | Authentication and role enforcement | **Not implemented** — out of scope | — |

---

## 2. Database status

Eight tables exist, matching the project diagram. Four carry business logic; four are schema-only
for later milestones.

| Table | Module | Status | Business logic |
| --- | --- | --- | --- |
| `leads` | 1 | **Live** | CRUD, import, search |
| `company_insights` | 2 | **Live** | Written on every analysis run |
| `lead_scores` | 4 | **Live** | Written on every analysis run |
| `outreach_campaigns` | 3 | **Live** | Written on every generation run |
| `users` | 5 | Schema only | — |
| `sales_interactions` | 5 | Schema only | — |
| `crm_sync_logs` | 5 | Schema only | — |
| `sales_analytics` | 6 | Schema only | — |

**Integrity.** Every child table references `leads.lead_id` with `ON DELETE CASCADE`. Foreign keys
are enforced in development (SQLite `PRAGMA foreign_keys=ON`) and in production (PostgreSQL native
constraint). Test TC-93 proves an orphan row is refused.

**Migrations.** Four numbered scripts applied in order and tracked in `schema_migrations`:

```
[applied] 001_initial_schema.sql
[applied] 002_intelligence_tables.sql
[applied] 003_outreach_campaigns.sql
[applied] 004_extended_tables.sql
```

Re-running the runner applies nothing (TC-91).

Full diagram: `docs/ER_DIAGRAM.md`.

---

## 3. API status

All 13 endpoints from `docs/API_CONTRACTS.md` are implemented and covered by the test suite.
TC-94 and TC-95 assert that the implementation and the contract contain exactly the same
endpoint set, so the document cannot drift from the code silently.

| Method | Endpoint | Status | Tests |
| --- | --- | --- | --- |
| GET | `/` | Live | — |
| GET | `/health` | Live | TC-12 |
| POST | `/api/leads` | Live | TC-01, TC-08 … TC-11 |
| GET | `/api/leads` | Live | TC-02, TC-03 |
| GET | `/api/leads/{lead_id}` | Live | TC-04, TC-07 |
| PUT | `/api/leads/{lead_id}` | Live | TC-05, TC-07 |
| DELETE | `/api/leads/{lead_id}` | Live | TC-06, TC-07 |
| POST | `/api/leads/import` | Live | TC-20 … TC-30 |
| GET | `/api/leads/{lead_id}/insights` | Live | TC-43, TC-45, TC-46 |
| GET | `/api/leads/stats` | Live | TC-12, TC-55 |
| POST | `/api/outreach/generate` | Live | TC-60 … TC-72 |
| GET | `/api/outreach` | Live | TC-68 |
| GET | `/api/leads/{lead_id}/outreach` | Live | TC-67, TC-68 |

Interactive documentation is served at `/docs`; the OpenAPI schema is at `/openapi.json`.

---

## 4. Lead import results

### 4.1 Clean import (`data/sample_leads.csv`, 4 rows)

```json
{
  "total_rows": 4,
  "inserted": 4,
  "updated": 0,
  "duplicates": 0,
  "rejected": 0,
  "inserted_lead_ids": [1, 2, 3, 4],
  "errors": []
}
```

### 4.2 Import with deliberate problems (`data/sample_leads_with_issues.csv`, 5 rows)

| Row | Problem | Reported reason | Outcome |
| --- | --- | --- | --- |
| 2 | — | — | Inserted |
| 3 | `email = not-an-email` | `invalid_email` | Rejected |
| 4 | `company_name` empty | `missing_company_name` | Rejected |
| 5 | `lead_status = Archived` | `invalid_status` | Rejected |
| 6 | Email already present | `duplicate_email` | Rejected as duplicate |

Every rejection carries the row number, the reason code and a message that states how to fix it.
A rejected row never prevents the valid rows from being stored (TC-23).

### 4.3 Duplicate policy

| Policy | Behaviour | Test |
| --- | --- | --- |
| `reject` (default) | The row is refused and reported as a rejected duplicate | TC-26 |
| `skip` | The row is reported as a duplicate and skipped; the file still succeeds | TC-27 |
| `update_existing` | An existing record is refreshed instead of a duplicate being reported | TC-31, TC-32, TC-33 |

---

## 5. Lead intelligence examples

### 5.1 Fully populated record

Input: `CloudScale Inc`, industry `Cloud Computing`, contact `Robert Wilson`,
`robert@example.com`, `501-1000`, status `New`.

**Qualification score: 90 / 100 — band `High`**

| Factor | Weight | Raw | Points | Explanation |
| --- | --- | --- | --- | --- |
| Industry relevance | 30 | 1.00 | 30.00 | `'Cloud Computing' is a configured target industry.` |
| Company size signal | 20 | 1.00 | 20.00 | `Company size band '501-1000' maps to fit factor 1.00.` |
| Contact data completeness | 25 | 1.00 | 25.00 | `5 of 5 key fields present.` |
| Engagement stage | 20 | 0.50 | 10.00 | `Status 'New' indicates engagement stage factor 0.50.` |
| Reachable channel | 5 | 1.00 | 5.00 | `A direct email address is recorded.` |

**Business needs**
- Qualify inbound cloud enquiries before a demo is scheduled
- Connect technical buying committees to a single record

**Sales opportunities**
- Lead scoring with explainable factors
- Outreach drafting that speaks to infrastructure teams
- Duplicate suppression across partner-sourced leads

**Key insights**
- Recorded industry 'Cloud Computing' maps to the 'cloud computing' sector reference.
- Sector-level buying triggers for 'cloud computing': cost optimisation programmes; multi-cloud adoption; migration projects.
- Record completeness is 100% across contact name, email, phone, industry and company size.
- Current pipeline status for this record is 'New'.
- A named contact (Robert Wilson) with a working email format is stored, so personalised outreach is possible.

**Information gaps**
- No engagement notes stored - intent signals are unknown.

### 5.2 Sparse record

Input: company only, no industry, contact, email, phone or notes.

**Qualification score: 10 / 100 — band `Low`**

**Information gaps**
- Industry not recorded - sector-specific analysis is generic.
- Company size not recorded - account-fit weighting cannot be applied.
- Contact name not recorded - outreach cannot be personalised by name.
- Email not recorded - the contact cannot be reached by email.
- Phone not recorded - no secondary outreach channel is available.
- No engagement notes stored - intent signals are unknown.

### 5.3 Grounding guarantee

The analysis never asserts a company fact that is not stored. Revenue, headcount, funding,
valuation and employee counts appear in no output — enforced by test TC-44, which scans the
insight text for those terms. Sector statements are explicitly framed as sector-level context
("Sector-level buying triggers for …"), and any fact that is missing is reported as a gap
instead of being filled in.

---

## 6. Record coverage (measured)

The acceptance criterion is: *"at least 95 % of prospect records should be manageable and
analysable"*.

```
Record coverage (%) = Successfully managed AND analysed eligible records ÷ Total eligible records × 100
```

**Measurement method** (`backend/scripts/measure_coverage.py`): every row of a generated dataset
is imported through the API, then retrieved, updated, re-analysed (insight + score) and deleted
through the API. Only a record that completes the whole cycle counts.

| Dataset size | Imported | Managed | Analysed | Managed AND analysed | **Coverage** | Threshold |
| --- | --- | --- | --- | --- | --- | --- |
| 100 records | 100 | 100 | 100 | 100 | **100.00 %** | PASS (≥ 95 %) |
| 500 records | 500 | 500 | 500 | 500 | **100.00 %** | PASS (≥ 95 %) |

Raw output of the 500-record run:

```
Eligible rows in the source dataset : 500
Rows imported without error         : 500
Rows rejected by validation         : 0

Eligible records                     : 500
Successfully managed (CRUD)          : 500
Successfully analysed (insights+score): 500
Managed AND analysed                 : 500
Record coverage (%)                  : 100.00%
Threshold check: PASS (>= 95%)
```

This is a measured result from a run of the system, not an estimate.

---

## 7. Test summary

| Suite | Tests | Result |
| --- | --- | --- |
| Lead CRUD API | 12 | All pass |
| CSV import and validation | 14 | All pass |
| Duplicate detection | 5 | All pass |
| Lead intelligence and scoring | 13 | All pass |
| AI outreach generation | 13 | All pass |
| Performance | 2 | All pass |
| Schema, migrations, foreign keys | 4 | All pass |
| API contract conformance | 3 | All pass |
| **Total** | **66** | **66 pass, 0 fail** |

Seven bugs were found and fixed during the cycle; all seven are listed with their root cause and
regression test in `docs/TEST_RESULTS.md` §10.

Manual evidence: backend boot, Swagger rendering, migration apply/status, the end-to-end
walkthrough script, the record-coverage measurement, and a Streamlit render check of all four
pages via `streamlit.testing.v1.AppTest` (0 exceptions on each page).

---

## 8. Demonstration checklist

**Environment**

- [x] Backend starts with `python -m uvicorn app.main:app --app-dir backend`
- [x] `GET /health` returns `healthy`
- [x] Database connectivity confirmed (migrations applied, sample data loaded)
- [x] Swagger UI at `/docs` shows all 13 operations
- [x] Streamlit starts with `python -m streamlit run frontend/app.py`

**Lead management**

- [x] Create a lead (Leads page → Add a lead, and `POST /api/leads`)
- [x] View the lead list with search and status filter
- [x] Update lead details (partial update, other fields preserved)
- [x] Delete a test lead (confirming the dependent rows are removed)
- [x] Validation and error messages are visible in the UI

**CSV import**

- [x] Upload `data/sample_leads.csv` — 4 rows inserted, counters shown
- [x] Upload `data/sample_leads_with_issues.csv` — per-row reasons shown in a table
- [x] Duplicate detection explained and demonstrated (email match, company + contact match)

**Lead intelligence**

- [x] Select a prospect and display the company summary, score with factor breakdown, opportunities, insights and gaps
- [x] The score is visibly explained and labelled as a rule-based heuristic

**Outreach (Milestone 2 first slice)**

- [x] Generate a draft with tone, length and goal options
- [x] Mock mode is visibly labelled when no provider key is configured
- [x] The draft is stored and retrievable with status `draft`

**Design presentation**

- [x] ER diagram (`docs/ER_DIAGRAM.md`)
- [x] Database schema and migrations
- [x] API contracts (`docs/API_CONTRACTS.md`)
- [x] Agent / pipeline architecture (`docs/AGENT_ARCHITECTURE.md`)
- [x] UI wireframes (`docs/UI_WIREFRAMES.md`)
- [x] Testing approach (`docs/TEST_RESULTS.md`)

---

## 9. Known limitations

| # | Limitation | Impact | Planned stage |
| --- | --- | --- | --- |
| L-1 | No authentication or role enforcement | Any client with network access can read and write prospect data | Milestone 3+ |
| L-2 | The qualification score is a rule-based heuristic, not a trained model | It ranks records by data completeness and configured fit, not by likelihood of purchase | Milestone 4 (learned model) |
| L-3 | Insights come from a static sector reference table, not live company research | Insights are generic per sector and do not reflect current company news or financials | Milestone 2 (research agent) |
| L-4 | The email draft is generated by a deterministic offline template when no LLM key is configured | The copy is serviceable but not model-written; it is labelled `is_mock=true` everywhere it appears | Resolved as soon as `LLM_API_KEY` is set |
| L-5 | No email sending workflow | Drafts must be sent manually | Milestone 3+ |
| L-6 | No CSV export, bulk edit or bulk delete | Large corrections need one call per record | Milestone 2+ |
| L-7 | Tests run against SQLite; the production target is PostgreSQL | Engine-specific behaviour (timezone handling in particular) is not exercised in CI | Add a PostgreSQL CI job |
| L-8 | `company_size` is a free-text bucket rather than a numeric headcount | A very specific size cannot be expressed | Milestone 4 |
| L-9 | Timestamps on the SQLite development database are naive | Cosmetic only; PostgreSQL is the documented production target | — |
| L-10 | No pagination cursor, only offset/limit | Deep pagination degrades on very large tables | Milestone 4 |

---

## 10. Screenshots and evidence

| Evidence | Location |
| --- | --- |
| Swagger API page | `http://127.0.0.1:8000/docs` (live) |
| Streamlit application | `http://127.0.0.1:8501` (live) |
| End-to-end walkthrough transcript | `python backend/scripts/demo_walkthrough.py` |
| Record-coverage measurement | `python backend/scripts/measure_coverage.py --rows 500` |
| Migration state | `python backend/scripts/migrate.py --status` |
| Test output | `docs/TEST_RESULTS.md` |
| Schema diagram | `docs/ER_DIAGRAM.md` |
| Architecture diagram | `docs/AGENT_ARCHITECTURE.md` |
| UI wireframes | `docs/UI_WIREFRAMES.md` |

Screen captures of the running application are added to `docs/screenshots/` when the demo is
recorded.

---

## 11. Remaining issues

| # | Issue | Severity | Owner | Status |
| --- | --- | --- | --- | --- |
| I-1 | The API is unauthenticated | High | Backend team | Open — later milestone |
| I-2 | No PostgreSQL CI job | Medium | DevOps | Open |
| I-3 | Insights are sector-generic | Medium | Intelligence team | Open — Milestone 2 |
| I-4 | The qualification score is not predictive | Medium | Analytics team | Open — Milestone 4 |
| I-5 | No bulk operations on leads | Low | Backend team | Open — Milestone 2 |
| I-6 | Deep pagination is offset-based | Low | Backend team | Open — Milestone 4 |

---

## 12. Review status

| Item | Status |
| --- | --- |
| Implementation complete for the Milestone 1 scope | **Yes** |
| Automated test suite green | **Yes — 66/66** |
| Documentation complete | **Yes** |
| Record coverage measured | **Yes — 100.00 %** |
| Submitted for review | **Yes** |
| Approved by the evaluator | **Pending — awaiting the evaluator's decision** |
