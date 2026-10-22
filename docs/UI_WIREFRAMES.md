# UI Wireframes — SalesGenie AI

Interface: Streamlit (`frontend/`). The wireframes below describe the layout that was
implemented; the text blocks are the actual on-screen labels.

---

## 1. Global layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  SalesGenie AI                                                               │
├────────────────┬─────────────────────────────────────────────────────────────┤
│ SIDEBAR        │  MAIN CONTENT                                              │
│                │                                                             │
│ SalesGenie AI  │                                                             │
│ AI Sales       │                                                             │
│ Assistant &    │                                                             │
│ Lead Intel.    │                                                             │
│                │                                                             │
│ [Backend URL]  │                                                             │
│ [Check         │                                                             │
│  connection]   │                                                             │
│                │                                                             │
│ ─────────      │                                                             │
│ Milestone 1    │                                                             │
│  implemented   │                                                             │
│ Milestone 2    │                                                             │
│  first slice   │                                                             │
│ Not in this    │                                                             │
│  release       │                                                             │
└────────────────┴─────────────────────────────────────────────────────────────┘
```

Streamlit's `frontend/pages/` folder produces the top-level navigation: **Leads**,
**Intelligence**, **Outreach**.

---

## 2. Home page (`frontend/app.py`)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  SalesGenie AI                                                               │
│  Manage prospect records, review company intelligence ...                    │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐               │
│  │ Total leads│ │ Scored     │ │ Average    │ │ Industries   │               │
│  │     42     │ │ leads   40 │ │ score 71.4 │ │ tracked    4 │               │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────┘               │
│                                                                              │
│  ┌───────────────────────────┐  ┌───────────────────────────┐                │
│  │ Leads by status           │  │ Leads by industry         │                │
│  │  (bar chart)              │  │  (bar chart)              │                │
│  └───────────────────────────┘  └───────────────────────────┘                │
│                                                                              │
│  Quick start                                                                 │
│  1. Open Leads and upload data/sample_leads.csv                             │
│  2. Open Intelligence, pick a lead ...                                      │
│  3. Open Outreach, generate a draft ...                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Leads page (`frontend/pages/leads.py`)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Leads                                                                        │
│  Import, search and maintain the prospect database.                          │
│                                                                              │
│  [Search company, contact or email ] [Status ▾] [Industry ]                 │
│  ────────────────────────────────────────────────────────────────────────────│
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ Import leads from CSV        │  │ Add a lead                           │  │
│  │ Required columns: company_   │  │ Company name *  [______________]     │  │
│  │ name, email ...              │  │ Industry         [______________]     │  │
│  │                              │  │ Company size    [▾]                   │  │
│  │ (Choose a CSV file)          │  │ Contact name    [______________]     │  │
│  │ (o) reject  ( ) skip         │  │ Email           [______________]     │  │
│  │ [Import CSV]                 │  │ Phone           [______________]     │  │
│  │                              │  │ Lead status     [▾]                   │  │
│  │ Inserted  4                  │  │ Notes           [______________]     │  │
│  │ Duplicates 0                 │  │ [Create lead]                        │  │
│  │ Rejected  1                  │  │                                      │  │
│  │ (row report table)           │  │                                      │  │
│  └──────────────────────────────┘  └──────────────────────────────────────┘  │
│  ────────────────────────────────────────────────────────────────────────────│
│  Leads (42)                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ lead_id │ company_name │ industry │ contact_name │ email │ status │ ... │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│  Select a lead to edit or delete  [ #1 - TechCorp Solutions ▾ ]             │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ Edit lead                    │  │ Delete lead                          │  │
│  │ Company name [____]          │  │ ⚠ Deleting also removes insights,    │  │
│  │ Status    [▾]                │  │   scores and outreach drafts.        │  │
│  │ [Save changes]               │  │ [x] I understand this cannot be undone│  │
│  │                              │  │ [Delete lead]                        │  │
│  └──────────────────────────────┘  └──────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Behaviour

| Element | Behaviour |
| --- | --- |
| Search box | Filters on company name, contact name or email (server-side) |
| Status / Industry | Exact-match filters (server-side) |
| CSV upload | Posts to `POST /api/leads/import`; shows inserted / duplicates / rejected counts and a per-row error table |
| Duplicate policy | `reject` (row is refused) or `skip` (row is reported and skipped) |
| Add lead | Posts to `POST /api/leads`; the backend message is shown verbatim on failure |
| Edit lead | `PUT /api/leads/{id}` with only the fields shown |
| Delete lead | `DELETE /api/leads/{id}` behind an explicit confirmation checkbox |

---

## 4. Intelligence page (`frontend/pages/intelligence.py`)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Lead Intelligence                                                            │
│  Company analysis and a transparent qualification score ...                  │
│                                                                              │
│  Select a prospect  [ #1 - TechCorp Solutions (Sarah Johnson) ▾ ]            │
│  [x] Re-run the analysis        [Load intelligence]                          │
│  ────────────────────────────────────────────────────────────────────────────│
│  TechCorp Solutions                                                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────────────┐  │
│  │ Industry   │ │ Contact    │ │ Status     │ │ Data completeness        │  │
│  │ Software   │ │ Sarah J.   │ │ New        │ │ 83%                      │  │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────────────────┘  │
│                                                                              │
│  Qualification score                                                         │
│  ┌──────────┐  Rule-based prioritisation heuristic ... not a trained model.  │
│  │ 78 / 100 │  Methodology: rule_based_v1                                    │
│  │ High     │                                                                 │
│  └──────────┘  ┌──────────────────────────────────────────────────────────┐  │
│                 │ name │ weight │ raw │ points │ explanation               │  │
│                 └──────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ Business needs             │  │ Key insights                         │  │
│  │  - Scale lead intake ...   │  │  - Recorded industry 'Software' ... │  │
│  │ Opportunities              │  │  - Record completeness is 83% ...   │  │
│  │  - Prospect database ...   │  │ Information gaps                    │  │
│  │                            │  │  - Company size not recorded ...     │  │
│  └────────────────────────────┘  └──────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Outreach page (`frontend/pages/outreach.py`)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  AI Outreach                                                                  │
│  Generate a personalised first-touch email ...                               │
│                                                                              │
│  Select a prospect  [ #1 - TechCorp Solutions (Sarah Johnson) ▾ ]            │
│                                                                              │
│  Draft options                                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                        │
│  │ Tone         │ │ Length       │ │ Goal         │                        │
│  │ professional │ │ short        │ │ Meeting      │                        │
│  └──────────────┘ └──────────────┘ └──────────────┘                        │
│  Product or service being offered *  [SalesGenie AI lead intelligence ...]   │
│  [Generate draft]                                                            │
│  ────────────────────────────────────────────────────────────────────────────│
│  Latest draft                                                                │
│  ⚠ This draft was produced by the offline mock generator, not by an AI model │
│  Subject                                                                     │
│  Scaling lead operations at TechCorp Solutions                              │
│  Body                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ Hi Sarah Johnson,                                                        │ │
│  │ ...                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│  Status: draft · Tone: professional · Length: short · Goal: meeting          │
│  ────────────────────────────────────────────────────────────────────────────│
│  Stored drafts (table: campaign_id, lead_id, subject, status, tone, is_mock) │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Mock-mode disclosure (required)

When no LLM provider key is configured, the page shows a warning that the draft came from the
offline generator. A mock draft is never presented as a real AI result.
