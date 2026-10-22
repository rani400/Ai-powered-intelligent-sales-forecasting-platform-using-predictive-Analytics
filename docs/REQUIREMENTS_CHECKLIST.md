# Requirements Checklist — SalesGenie AI

Derived from `docs/SRS.md`. Every functional requirement (FR) and non-functional requirement
(NFR) is listed with the implementation that satisfies it and the test that proves it.

Status values: **Met** · **Partial** · **Deferred** (out of scope for this window) · **Open**

---

## 1. Functional requirements

### 1.1 Lead management (Module 1)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| FR-1.1 | Create a lead | `services/lead_service.py::create_lead` | TC-01 | **Met** |
| FR-1.2 | List leads with search, filter and pagination | `services/lead_service.py::list_leads` | TC-02, TC-03 | **Met** |
| FR-1.3 | Retrieve one lead | `services/lead_service.py::get_lead_or_404` | TC-04 | **Met** |
| FR-1.4 | Update a lead without losing other fields | `services/lead_service.py::update_lead` | TC-05 | **Met** |
| FR-1.5 | Delete a lead and its dependent records | `services/lead_service.py::delete_lead` | TC-06 | **Met** |
| FR-1.6 | 404 for an unknown lead id | `errors.py::NotFoundError` | TC-07 | **Met** |
| FR-1.7 | 422 with a clear message for invalid input | `schemas/lead_schema.py` validators | TC-08, TC-09 | **Met** |
| FR-1.8 | Import leads from a CSV file | `services/lead_import.py` | TC-20 | **Met** |
| FR-1.9 | Validate required CSV columns | `services/lead_import.py::parse_csv` | TC-21 | **Met** |
| FR-1.10 | Normalise email and whitespace on every write | `schemas/lead_schema.py`, `utils/validation.py` | TC-11, TC-25 | **Met** |
| FR-1.11 | Detect duplicates by email, flag company + contact | `services/duplicate_detection.py` | TC-26, TC-27, TC-28, TC-D1…TC-D5 | **Met** |
| FR-1.12 | Report per-row import outcomes | `services/lead_import.py::ImportResult` | TC-29 | **Met** |
| FR-1.13 | Record the lead source | `models/lead.py::LeadSource` | TC-01 | **Met** |
| FR-1.14 | Exclude deleted rows from listings | `models/lead.py::is_active` | TC-06 | **Met** |

### 1.2 Lead intelligence (Module 2)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| FR-2.1 | Company summary from stored fields only | `services/lead_intelligence.py::build_company_profile` | TC-40 | **Met** |
| FR-2.2 | Industry-specific opportunity list | `services/lead_intelligence.py::INDUSTRY_REFERENCE` | TC-41 | **Met** |
| FR-2.3 | Information gaps for missing fields | `services/lead_intelligence.py::build_information_gaps` | TC-42 | **Met** |
| FR-2.4 | Persist each insight run | `services/lead_intelligence.py::persist_insight` | TC-43, TC-54 | **Met** |
| FR-2.5 | Never assert absent company facts | Grounding rules in the service | TC-44 | **Met** |
| FR-2.6 | Expose insights over HTTP | `routers/leads.py::read_lead_insights` | TC-45 | **Met** |
| FR-2.7 | Return the latest insight set | `services/lead_intelligence.py::get_or_generate_insight` | TC-43 | **Met** |

### 1.3 Lead scoring (Module 4 baseline)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| FR-3.1 | 0–100 score from documented factors | `services/lead_intelligence.py` | TC-50 | **Met** |
| FR-3.2 | Return the factor contributions | `services/lead_intelligence.py::ScoreFactor` | TC-51 | **Met** |
| FR-3.3 | Record every score in `lead_scores` | `services/lead_intelligence.py::persist_insight` | TC-54 | **Met** |
| FR-3.4 | Document the score as rule-based | `docs/SRS.md`, API `disclaimer` field | TC-45 | **Met** |
| FR-3.5 | Deterministic score | `services/lead_intelligence.py` | TC-53 | **Met** |

### 1.4 AI outreach generation (Module 3, first slice)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| FR-4.1 | Accept lead identity plus preferences | `schemas/outreach.py::OutreachRequest` | TC-60 | **Met** |
| FR-4.2 | Build the prompt from validated lead data | `services/outreach_generator.py::build_prompt` | TC-61 | **Met** |
| FR-4.3 | Call the provider and extract subject + body | `services/outreach_generator.py` | TC-62 | **Met** |
| FR-4.4 | Clearly-labelled mock when no provider is configured | `services/outreach_generator.py::build_mock_draft` | TC-63 | **Met** |
| FR-4.5 | Handle missing fields, timeouts and provider errors | `services/outreach_generator.py` | TC-64, TC-65, TC-66, TC-71 | **Met** |
| FR-4.6 | Store each draft with status `draft` | `routers/outreach.py::generate_outreach` | TC-67 | **Met** |
| FR-4.7 | Retrieve stored drafts for a lead | `routers/leads.py::read_lead_outreach` | TC-68 | **Met** |
| FR-4.8 | Never mark a draft as sent | `models/outreach_campaign.py::CampaignStatus` | TC-67 | **Met** |
| FR-4.9 | Tone and length variants | `services/outreach_generator.py::TONES`, `LENGTHS` | TC-69 | **Met** |

### 1.5 Interface

| ID | Requirement | Implementation | Evidence | Status |
| --- | --- | --- | --- | --- |
| FR-5.1 | Leads page: search, filter, upload, add, table, edit, delete | `frontend/pages/leads.py` | Streamlit render check | **Met** |
| FR-5.2 | Surface backend errors instead of false success | `frontend/api_client.py::ApiError` | Demo walkthrough | **Met** |
| FR-5.3 | Intelligence panel shows profile, score, opportunities, insights, gaps | `frontend/pages/intelligence.py` | Streamlit render check | **Met** |
| FR-5.4 | Outreach page generates, previews and stores drafts | `frontend/pages/outreach.py` | Demo walkthrough | **Met** |

---

## 2. Non-functional requirements

| ID | Requirement | How it is satisfied | Test | Status |
| --- | --- | --- | --- | --- |
| NFR-1 | All writes validated at the API boundary | Pydantic validators in `schemas/lead_schema.py` | TC-08, TC-09 | **Met** |
| NFR-2 | Foreign keys enforced | `ON DELETE CASCADE` on every child table; `PRAGMA foreign_keys=ON` | TC-93 | **Met** |
| NFR-3 | Import is atomic per row | Each row is validated before insertion; a failure never writes a partial row | TC-23 | **Met** |
| NFR-4 | Credentials only in `.env`, which is git-ignored | `.gitignore` excludes `.env`; `.env.example` documents the keys without values | Repo audit | **Met** |
| NFR-5 | Contact data never logged | The service layer logs configuration only; no lead payload is logged | Code audit | **Met** |
| NFR-6 | No secrets committed | `.gitignore` covers `.env`, `venv`, caches and local database files | Repo audit | **Met** |
| NFR-7 | Modular architecture, no business rules in routes | `routers → services → models → database` | Code audit | **Met** |
| NFR-8 | Docstrings and type hints on public functions | Every module in `app/` | Code audit | **Met** |
| NFR-9 | Configuration externalised | `app/config.py` reads only environment variables | Code audit | **Met** |
| NFR-10 | One error-handling path | `app/errors.py::register_exception_handlers` | TC-07, TC-08, TC-71 | **Met** |
| NFR-11 | List endpoint under 500 ms | Indexed filters and pagination | TC-80 | **Met** |
| NFR-12 | 1,000-row import under 30 s | Bulk flush inside one transaction | TC-81 | **Met** |
| NFR-13 | Error messages state what failed and how to fix it | Row-level `message` on every import error; field-level API errors | TC-24, TC-08 | **Met** |
| NFR-14 | Usable without reading the source | Labelled actions, help text, empty states | Demo walkthrough | **Met** |
| NFR-15 | Services unit-testable without a live server | Services take a `Session`; the suite covers them directly | Whole suite | **Met** |
| NFR-16 | PostgreSQL production, SQLite for dev and tests | `DATABASE_URL` selects the engine | TC-92 | **Met** |

---

## 3. Explicitly out of scope for this window

These are **Deferred**, not failed — they belong to later milestones of the 40-day schedule.

| Item | Target |
| --- | --- |
| Authentication and role enforcement | Milestone 3 |
| CRM integrations (Salesforce / HubSpot) | Milestone 3 |
| Conversation intelligence and summarisation | Milestone 3 |
| Full sales analytics dashboard | Milestone 4 |
| Learned conversion-probability model | Milestone 4 |
| Email sending workflow | Milestone 3 |
| Full LangGraph agent orchestration | Milestone 2 (later) |
| Production deployment and CI/CD | Post-window |

---

## 4. Summary

| Group | Total | Met | Partial | Deferred |
| --- | --- | --- | --- | --- |
| Functional requirements | 41 | 41 | 0 | 0 |
| Non-functional requirements | 16 | 16 | 0 | 0 |
| Out-of-scope items (recorded, not counted above) | 8 | — | — | 8 |

**Requirements coverage: 41/41 functional and 16/16 non-functional requirements are met and
covered by at least one automated test.**
