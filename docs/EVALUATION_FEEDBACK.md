# Evaluation Feedback and Issue Log — Milestone 1

**Milestone:** 1 — Lead Management & Intelligence Engine
**Demo date:** 21 October 2026 (plan) · **Log opened:** 21 October 2026
**Status:** open

---

## 1. How to read this log

This file records issues found during the Milestone 1 demonstration and the self-review that
accompanied it. Each entry has a description, a severity, an owner, a planned fix and a status.

**Severity scale**

| Severity | Meaning |
| --- | --- |
| Critical | A core workflow is broken or produces incorrect data |
| High | A core workflow is degraded, or data integrity is at risk |
| Medium | A feature works but is incomplete or awkward to use |
| Low | Cosmetic, documentation or internal-quality issue |

**Status values:** `Open` · `In progress` · `Fixed` · `Deferred` · `Accepted (not fixed)`

> **Evaluator feedback:** no external evaluator feedback has been recorded yet. Section 4 is the
> place to add it, using the same table format. Nothing in this file should be read as an
> evaluator's assessment.

---

## 2. Issues found during the demonstration

| # | Description | Severity | Owner | Planned fix | Status |
| --- | --- | --- | --- | --- | --- |
| E-01 | `PUT /api/leads/{lead_id}` with an empty body returns 422 rather than 404 for an unknown lead | Low | Backend team | Keep the 422 — an empty update body is genuinely invalid. The demo script now sends a valid body when probing an unknown id | **Fixed** (test TC-07 updated to assert the documented behaviour) |
| E-02 | `company_name` retained internal double spaces (`"TechCorp   Solutions"`) | High | Backend team | Normalise with the same whitespace-collapsing helper used for every other field | **Fixed** (B-03) |
| E-03 | Duplicate detection crashed with `AttributeError` on the company + contact path | Critical | Backend team | `Select.scalars()` does not exist in SQLAlchemy 2.0; call `scalars()` on the result instead | **Fixed** (B-01) |
| E-04 | `GET /api/leads` returned a 500 instead of a list — the response schema could not resolve `LeadRead` | Critical | Backend team | Import `LeadRead` into `schemas/lead_schema.py` so the forward reference resolves | **Fixed** (B-02) |
| E-05 | The dashboard showed "2 scored leads" for a single scored prospect | Medium | Backend team | Count distinct lead ids instead of score rows | **Fixed** (B-05) |
| E-06 | The import report counted a skipped duplicate as both a duplicate and a rejected row under the `reject` policy | Medium | Backend team | Decided and documented: under `reject` a duplicate is both counted and rejected, because the row was refused. Under `skip` it is counted as a duplicate only. The report states the policy used | **Accepted (documented)** |
| E-07 | The qualification score could be read as a conversion probability | High | Analytics team | Add an explicit disclaimer to the API payload, the UI and the documentation | **Fixed** |
| E-08 | Insights could be read as facts about the specific company | High | Intelligence team | Sector statements are now explicitly framed as sector-level context, missing facts are reported as gaps, and a test forbids revenue/headcount/funding claims | **Fixed** (TC-44) |
| E-09 | The mock outreach draft looked like a real AI-generated email | High | AI team | Every mock draft carries `is_mock=true`, `provider="mock"` and a note stating it came from the offline generator. The UI shows a warning | **Fixed** (TC-63) |
| E-10 | The API had no authentication | High | Backend team | Out of scope for this window | **Deferred** to Milestone 3 |
| E-11 | The qualification score treats a missing company size as zero points, which is harsher than the "unknown" case deserves | Medium | Analytics team | Keep for now — the missing-field penalty is deliberate and visible in the factor explanation | **Accepted (documented)** |
| E-12 | The Swagger page had no worked example body | Low | Backend team | Request and response examples are documented in `docs/API_CONTRACTS.md` | **Fixed** |
| E-13 | The record-coverage figure could have been asserted rather than measured | High | QA | A measurement script now imports, manages and analyses every record and computes the percentage | **Fixed** (`backend/scripts/measure_coverage.py`, 100.00 % over 500 records) |
| E-14 | Timestamps on the SQLite development database are naive | Low | Backend team | PostgreSQL is the documented production target; the migration runner expands `TIMESTAMPTZ` for it | **Accepted (documented)** |
| E-15 | No PostgreSQL job in continuous integration | Medium | DevOps | Add a PostgreSQL test job | **Deferred** |

---

## 3. Defect log

| # | Defect | Severity | Owner | Planned fix | Status |
| --- | --- | --- | --- | --- | --- |
| B-01 | `Select.scalars()` `AttributeError` in duplicate detection | Critical | Backend team | Use `db.execute(...).scalars().first()` | **Fixed** |
| B-02 | `LeadListResponse` validation failure | Critical | Backend team | Resolve the `LeadRead` forward reference | **Fixed** |
| B-03 | Internal whitespace preserved in `company_name` | High | Backend team | Collapse whitespace via `_normalise_text` | **Fixed** |
| B-04 | Empty `PUT` body produced a 422 before the 404 path | Low | Backend team | Documented behaviour; demo script corrected | **Fixed** |
| B-05 | `scored_leads` counted rows rather than leads | Medium | Backend team | `count(distinct(lead_id))` | **Fixed** |
| B-06 | Naive timestamps on SQLite | Low | Backend team | Documented; PostgreSQL is the production target | **Accepted** |
| B-07 | `update_existing` did not copy `lead_status` | Medium | Backend team | Copy `lead_status` in the update branch; add TC-31 … TC-33 | **Fixed** |

---

## 4. Evaluator feedback

*No external evaluator feedback recorded yet. Add rows below using the same table format.*

| # | Description | Severity | Owner | Planned fix | Status |
| --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — |

---

## 5. Items closed by the fixes

| Issue | Verified by |
| --- | --- |
| E-02 / B-03 | TC-11 |
| E-03 / B-01 | TC-D2, TC-D3 |
| E-04 / B-02 | TC-02, TC-03 |
| E-05 / B-05 | TC-55 |
| E-07 | TC-45 (disclaimer present) |
| E-08 | TC-44 |
| E-09 | TC-63, TC-67 |
| E-13 | `measure_coverage.py --rows 500` → 100.00 % |
| B-07 | TC-31, TC-32, TC-33 |

---

## 6. Items carried into the next milestone

| Item | Severity | Target milestone |
| --- | --- | --- |
| E-10 Authentication and roles | High | Milestone 3 |
| E-15 PostgreSQL CI job | Medium | Milestone 2 |
| L-3 Live company research for insights | Medium | Milestone 2 |
| L-5 Email sending workflow | Medium | Milestone 3 |
| L-6 Bulk lead operations | Low | Milestone 2 |
| Learned conversion model | Medium | Milestone 4 |
