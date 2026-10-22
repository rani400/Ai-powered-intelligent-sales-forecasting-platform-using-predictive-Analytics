# Sprint Plan — SalesGenie AI

**Sprint:** 12 October 2026 → 21 October 2026 (10 days)
**Milestone:** 1 — Lead Management & Intelligence Engine, plus the first slice of Milestone 2
**Working day:** 1 (hours) · **Story point scale:** 1 = small, 2 = medium, 3 = large

---

## 1. Sprint goal

Deliver a tested lead management and lead intelligence workflow end to end, submit Milestone 1
for review, and start the AI outreach generation module.

**Definition of done for the sprint**

1. Lead CRUD, CSV import and duplicate detection work through both the API and the UI.
2. Every eligible prospect record can be managed and analysed, with the coverage figure measured
   rather than asserted.
3. The automated test suite is green and the results are recorded.
4. Milestone 1 documentation is complete and the milestone is submitted for review.
5. The first implementation of AI outreach generation and draft storage is working.

---

## 2. Backlog

### Sprint 1 — Milestone 1: Lead Management & Intelligence Engine

| ID | Task | Owner | Points | Days | Status |
| --- | --- | --- | --- | --- | --- |
| SG-1.1 | Requirements analysis, module list and project scope | Backend + BA | 3 | Day 1 | **Done** |
| SG-1.2 | Write `docs/SRS.md` with functional and non-functional requirements | Backend + BA | 3 | Day 1 | **Done** |
| SG-1.3 | Create the repository structure, `.gitignore`, `.env.example` | Backend | 1 | Day 2 | **Done** |
| SG-1.4 | Define the API contracts in `docs/API_CONTRACTS.md` | Backend | 2 | Day 2 | **Done** |
| SG-1.5 | Set up the Python environment and dependency manifest | Backend | 1 | Day 2 | **Done** |
| SG-1.6 | Bootstrap the FastAPI application and the Streamlit page | Backend + Frontend | 1 | Day 2 | **Done** |
| SG-1.7 | Design the database schema and write `docs/ER_DIAGRAM.md` | Backend | 3 | Day 3 | **Done** |
| SG-1.8 | Prepare the UI wireframes | Frontend | 2 | Day 3 | **Done** |
| SG-1.9 | Document the agent / pipeline architecture | Backend | 2 | Day 3 | **Done** |
| SG-1.10 | Implement the SQLAlchemy models for leads | Backend | 2 | Day 4 | **Done** |
| SG-1.11 | Write the versioned migrations and the migration runner | Backend | 2 | Day 4 | **Done** |
| SG-1.12 | Implement the lead CRUD endpoints | Backend | 3 | Day 4 | **Done** |
| SG-1.13 | Add request validation and the shared error envelope | Backend | 2 | Day 4 | **Done** |
| SG-1.14 | Prepare the sample dataset | Backend | 1 | Day 5 | **Done** |
| SG-1.15 | Implement the CSV import service | Backend | 3 | Day 5 | **Done** |
| SG-1.16 | Implement duplicate detection | Backend | 2 | Day 5 | **Done** |
| SG-1.17 | Build the Streamlit Leads page | Frontend | 3 | Day 5 | **Done** |
| SG-1.18 | Connect the frontend to the backend with real error handling | Frontend | 2 | Day 5 | **Done** |
| SG-1.19 | Write the unit tests for leads, import and duplicates | QA | 3 | Day 6 | **Done** |
| SG-1.20 | Validate the sample dataset and check database consistency | QA | 2 | Day 6 | **Done** |
| SG-1.21 | Record the test results and fix the bugs found | QA | 2 | Day 6 | **Done** |
| SG-1.22 | Implement the company analysis and insight generation | Backend | 3 | Day 7 | **Done** |
| SG-1.23 | Implement the rule-based qualification score | Backend | 2 | Day 7 | **Done** |
| SG-1.24 | Connect the intelligence panel to the UI | Frontend | 2 | Day 7 | **Done** |
| SG-1.25 | Write the Milestone 1 report and demo checklist | Backend + BA | 2 | Day 7 | **Done** |
| SG-1.26 | Prepare and rehearse the demonstration | Whole team | 1 | Day 8 | **Done** |
| SG-1.27 | Record the evaluation feedback and fix the critical issues | Whole team | 2 | Day 8 | **Done** |
| SG-1.28 | Run the regression suite | QA | 1 | Day 9 | **Done** |
| SG-1.29 | Measure the prospect record coverage | QA | 1 | Day 9 | **Done** |
| SG-1.30 | Finalise the documentation and prepare the submission package | Backend + BA | 2 | Day 9 | **Done** |

### Sprint 2 opening — Milestone 2: AI Outreach Generation

| ID | Task | Owner | Points | Days | Status |
| --- | --- | --- | --- | --- | --- |
| SG-2.1 | Define the outreach generation request structure | Backend | 1 | Day 10 | **Done** |
| SG-2.2 | Write the reusable prompt templates | Backend | 2 | Day 10 | **Done** |
| SG-2.3 | Implement the outreach generation service with a labelled mock fallback | Backend | 3 | Day 10 | **Done** |
| SG-2.4 | Create the outreach campaign model and migration | Backend | 2 | Day 10 | **Done** |
| SG-2.5 | Implement `POST /api/outreach/generate` | Backend | 2 | Day 10 | **Done** |
| SG-2.6 | Store and retrieve the generated drafts | Backend | 2 | Day 10 | **Done** |
| SG-2.7 | Test the outreach service | QA | 2 | Day 10 | **Done** |

---

## 3. Total points

| Sprint | Points |
| --- | --- |
| Sprint 1 — Milestone 1 | 62 |
| Sprint 2 opening — Milestone 2 first slice | 14 |
| **Total committed** | **76** |

---

## 4. Risks

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| PostgreSQL is not available in the development environment | High | Medium | `DATABASE_URL` selects the engine; SQLite is supported for development and tests, PostgreSQL is the documented production target |
| No LLM provider credentials are available | High | Medium | The service falls back to a clearly-labelled deterministic generator; the real provider path is covered by a mocked transport |
| The qualification score is mistaken for a predictive model | Medium | High | Disclaimer in the API payload, the UI, the SRS and the milestone report |
| The scope expands into CRM and analytics | Medium | High | Scope boundary recorded in `docs/SRS.md` §4.2 and in `docs/DAY_PLAN.md` |
| Duplicate rules are too strict for real prospect lists | Medium | Medium | Two policies (`reject` / `skip`) and a softer company + contact signal for review |

---

## 5. Ceremonies and artefacts

| Artefact | Location |
| --- | --- |
| Requirements | `docs/SRS.md` |
| API contracts | `docs/API_CONTRACTS.md` |
| Database design | `docs/ER_DIAGRAM.md` |
| UI design | `docs/UI_WIREFRAMES.md` |
| Architecture | `docs/AGENT_ARCHITECTURE.md` |
| Test results | `docs/TEST_RESULTS.md` |
| Milestone report | `docs/MILESTONE_1_REPORT.md` |
| Feedback log | `docs/EVALUATION_FEEDBACK.md` |
| Day-by-day status | `docs/DAY_PLAN.md` |
| Technology decisions | `docs/TECH_STACK.md` |
