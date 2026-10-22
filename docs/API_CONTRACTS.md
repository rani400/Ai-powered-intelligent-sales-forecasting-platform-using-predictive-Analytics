# API Contracts — SalesGenie AI

**Base URL:** `http://127.0.0.1:8000` · **API prefix:** `/api` · **Interactive docs:** `http://127.0.0.1:8000/docs`

This document is the **proposed contract for the implementation** in `backend/app/routers/`. Every
endpoint listed here is implemented and covered by a test in `backend/tests/` unless a row in the
Status column says otherwise. The FastAPI-generated OpenAPI document at `/docs` is the runtime
source of truth; this file is the design contract.

---

## 1. Conventions

| Topic | Rule |
| --- | --- |
| Content type | `application/json`, except `POST /api/leads/import` which uses `multipart/form-data` |
| Identifiers | `lead_id` and `campaign_id` are positive integers |
| Timestamps | ISO-8601, timezone-aware UTC, e.g. `2026-10-12T09:30:00Z` |
| Date format | `YYYY-MM-DD` |
| Errors | JSON body `{ "detail": <string>, "errors": [ { "field": ..., "message": ... } ] }` |
| Validation failure | `422 Unprocessable Entity` |
| Missing resource | `404 Not Found` |
| Conflict (duplicate) | `409 Conflict` |
| Server error | `500 Internal Server Error` with a generic message (no stack trace in the body) |

### 1.1 Lead status values

`New` · `Contacted` · `Qualified` · `Unqualified` · `Converted` · `Lost`

Status matching is case-insensitive on input and normalised to the canonical capitalisation above
on write.

### 1.2 Lead source values

`manual` · `csv_import`

---

## 2. Field reference — Lead

| Field | Type | Required on create | Rules |
| --- | --- | --- | --- |
| `lead_id` | integer | auto | Primary key, read-only |
| `company_name` | string | yes | 1–200 chars, trimmed, not blank |
| `industry` | string | no | ≤ 120 chars, trimmed |
| `contact_name` | string | no | ≤ 120 chars, trimmed |
| `email` | string | no | RFC-style validation when present, lower-cased, trimmed |
| `phone` | string | no | ≤ 40 chars; digits, spaces, `+`, `-`, `(`, `)` allowed |
| `lead_status` | string | no | One of the status values above; defaults to `New` |
| `notes` | string | no | ≤ 2000 chars |
| `source` | string | no | `manual` or `csv_import`; defaults to `manual` |
| `is_active` | boolean | no | Defaults to `true` |
| `created_at` | datetime | auto | Read-only |
| `updated_at` | datetime | auto | Read-only |

---

## 3. Endpoints

### 3.1 `GET /health` — Service health

Not under the `/api` prefix. Returns `200`:

```json
{ "status": "healthy", "service": "SalesGenie AI", "version": "1.0.0" }
```

---

### 3.2 `POST /api/leads` — Create a lead

**Purpose:** create one validated prospect record.

**Request body**

```json
{
  "company_name": "TechCorp Solutions",
  "industry": "Software",
  "contact_name": "Sarah Johnson",
  "email": "sarah@example.com",
  "phone": "9876543210",
  "lead_status": "New",
  "notes": "Referred at the Q3 analytics summit"
}
```

**Responses**

| Status | Body | When |
| --- | --- | --- |
| `201` | Lead object | Created |
| `422` | Error body | Missing `company_name`, malformed email, unknown status |
| `409` | Error body | A lead with the same normalised email already exists |

**Example response (`201`)**

```json
{
  "lead_id": 1,
  "company_name": "TechCorp Solutions",
  "industry": "Software",
  "contact_name": "Sarah Johnson",
  "email": "sarah@example.com",
  "phone": "9876543210",
  "lead_status": "New",
  "notes": "Referred at the Q3 analytics summit",
  "source": "manual",
  "is_active": true,
  "created_at": "2026-10-12T09:30:00Z",
  "updated_at": "2026-10-12T09:30:00Z"
}
```

---

### 3.3 `GET /api/leads` — Retrieve leads

**Purpose:** list prospect records with search, filtering and pagination.

**Query parameters**

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `search` | string | — | Case-insensitive match on company name, contact name or email |
| `status` | string | — | Filter by exact lead status |
| `industry` | string | — | Filter by exact industry |
| `skip` | integer | `0` | Rows to skip |
| `limit` | integer | `50` | Page size, max `200` |

**Responses:** `200` with

```json
{
  "total": 4,
  "skip": 0,
  "limit": 50,
  "items": [ { "lead_id": 1, "...": "..." } ]
}
```

---

### 3.4 `GET /api/leads/{lead_id}` — Retrieve one lead

**Responses:** `200` Lead object · `404` `{"detail": "Lead 999 not found"}`

---

### 3.5 `PUT /api/leads/{lead_id}` — Update a lead

**Purpose:** partial update of a lead. Only the fields present in the body are modified.

**Request body** — any subset of the writable lead fields.

```json
{ "lead_status": "Qualified", "notes": "Budget confirmed" }
```

**Responses:** `200` updated Lead object · `404` unknown ID · `422` invalid field · `409` email collision with another lead.

---

### 3.6 `DELETE /api/leads/{lead_id}` — Delete a lead

**Purpose:** remove a lead and its dependent insight, score and outreach rows.

**Responses:** `200` `{"detail": "Lead 1 deleted", "lead_id": 1}` · `404` unknown ID

---

### 3.7 `POST /api/leads/import` — Import CSV leads

**Purpose:** bulk import prospect records with per-row validation and duplicate handling.

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file` | file | yes | CSV upload |
| `duplicate_policy` | string | no | `reject` (default) or `skip` |
| `update_existing` | boolean | no | Default `false` |

**Required CSV columns:** `company_name`, `email`. Optional: `industry`, `contact_name`, `phone`,
`lead_status`, `notes`.

**Responses**

| Status | Body | When |
| --- | --- | --- |
| `200` | Import report (below) | File parsed, at least one row accepted or all rows rejected per-row |
| `400` | `{"detail": "..."}` | File is empty, not a CSV, or missing required columns |
| `422` | Error body | Upload field missing entirely |

**Import report**

```json
{
  "total_rows": 4,
  "inserted": 3,
  "updated": 0,
  "duplicates": 1,
  "rejected": 0,
  "errors": [
    { "row_number": 5, "email": "dup@example.com", "reason": "duplicate_email", "message": "A lead with this email already exists (lead_id 2)" }
  ],
  "inserted_lead_ids": [7, 8, 9]
}
```

`reason` is one of: `missing_company_name`, `missing_email`, `invalid_email`, `invalid_status`,
`duplicate_email`, `duplicate_company_contact`, `invalid_row`.

---

### 3.8 `GET /api/leads/{lead_id}/insights` — Retrieve lead intelligence

**Purpose:** run (or return the cached) company analysis and qualification score for a lead.

**Query parameters**

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| `refresh` | boolean | `false` | `true` re-runs the analysis and writes a new insight + score row |

**Responses:** `200`

```json
{
  "lead_id": 1,
  "generated_at": "2026-10-12T09:31:00Z",
  "company_profile": {
    "company_name": "TechCorp Solutions",
    "industry": "Software",
    "contact_name": "Sarah Johnson",
    "email": "sarah@example.com",
    "lead_status": "New",
    "data_completeness": 0.83
  },
  "qualification_score": {
    "score": 78,
    "band": "High",
    "factors": [
      { "name": "Industry relevance", "weight": 30, "raw_value": 1.0, "points_awarded": 30, "explanation": "Software is a target industry" },
      { "name": "Contact data completeness", "weight": 25, "raw_value": 0.83, "points_awarded": 21, "explanation": "5 of 6 key fields present" },
      { "name": "Lead status", "weight": 20, "raw_value": 0.5, "points_awarded": 10, "explanation": "Status 'New' indicates early-stage engagement" }
    ]
  },
  "business_needs": ["Scale lead intake operations", "Reduce manual data entry effort"],
  "opportunities": ["Sales operations automation", "Lead enrichment workflow"],
  "key_insights": [
    "Software sector: typical buying triggers are scale, security and integration requirements.",
    "Contact data completeness is 83%: email and contact name are available."
  ],
  "information_gaps": ["Company size not recorded", "No engagement history stored"]
}
```

**Other responses:** `404` unknown lead ID.

---

### 3.9 `POST /api/outreach/generate` — Generate an outreach draft

**Purpose:** produce a personalised first-touch email for a lead.

**Request body**

```json
{
  "lead_id": 1,
  "product_or_service": "SalesGenie AI lead intelligence platform",
  "communication_goal": "meeting",
  "tone": "professional",
  "email_length": "short"
}
```

| Field | Type | Required | Allowed values |
| --- | --- | --- | --- |
| `lead_id` | integer | yes | must exist |
| `company_name` | string | no | overrides the stored value when supplied |
| `contact_name` | string | no | overrides the stored value when supplied |
| `industry` | string | no | overrides the stored value when supplied |
| `product_or_service` | string | yes | 1–300 chars |
| `communication_goal` | string | no | `product_introduction` (default), `meeting`, `follow_up` |
| `tone` | string | no | `professional` (default), `friendly` |
| `email_length` | string | no | `short` (default), `detailed` |

**Responses**

| Status | Body | When |
| --- | --- | --- |
| `200` | Draft object | Generated |
| `404` | Error body | Unknown `lead_id` |
| `422` | Error body | Invalid tone / goal / length |
| `502` | Error body | LLM provider failed, timed out or returned an unusable response |

**Draft object**

```json
{
  "campaign_id": 1,
  "lead_id": 1,
  "email_subject": "Scaling lead operations at TechCorp Solutions",
  "email_content": "Hi Sarah Johnson,\n\n...",
  "campaign_status": "draft",
  "tone": "professional",
  "email_length": "short",
  "communication_goal": "meeting",
  "provider": "mock",
  "is_mock": true,
  "created_at": "2026-10-21T10:00:00Z",
  "notes": "Generated in mock mode: no LLM provider configured."
}
```

> `is_mock: true` means the content came from the labelled offline generator, not from a real LLM.
> A draft is only ever stored with `campaign_status: "draft"` — nothing is marked `sent` because no
> sending workflow exists in this scope.

---

### 3.10 `GET /api/outreach` — List outreach drafts

**Query parameters:** `lead_id` (optional filter) · `skip` (default `0`) · `limit` (default `50`)

**Responses:** `200` `{"total": 1, "skip": 0, "limit": 50, "items": [ { "campaign_id": 1, "...": "..." } ]}`

---

### 3.11 `GET /api/leads/{lead_id}/outreach` — Drafts for one lead

**Responses:** `200` `{"lead_id": 1, "total": 1, "items": [ ...drafts ]}` · `404` unknown lead ID

---

### 3.12 `GET /api/leads/stats` — Operational counters

**Purpose:** lightweight dashboard counters for the Streamlit home page. This is **not** the full
sales analytics module (out of scope for this window).

**Responses:** `200`

```json
{
  "total_leads": 42,
  "active_leads": 42,
  "by_status": { "New": 30, "Qualified": 12 },
  "by_industry": { "Software": 18, "Analytics": 24 },
  "average_score": 71.4,
  "scored_leads": 42
}
```

---

## 4. Error body format

```json
{
  "detail": "Request validation failed",
  "errors": [
    { "field": "email", "message": "value is not a valid email address" },
    { "field": "company_name", "message": "company_name is required" }
  ]
}
```

Single-error responses use the same shape with one entry in `errors`, and `detail` carries the
human-readable summary.

---

## 5. Endpoint summary

| Method | Endpoint | Purpose | Status |
| --- | --- | --- | --- |
| GET | `/` | Service banner (service, version, docs link) | Implemented |
| GET | `/health` | Service health | Implemented |
| POST | `/api/leads` | Create a lead | Implemented |
| GET | `/api/leads` | Retrieve leads | Implemented |
| GET | `/api/leads/{lead_id}` | Retrieve one lead | Implemented |
| PUT | `/api/leads/{lead_id}` | Update a lead | Implemented |
| DELETE | `/api/leads/{lead_id}` | Delete a lead | Implemented |
| POST | `/api/leads/import` | Import CSV leads | Implemented |
| GET | `/api/leads/{lead_id}/insights` | Retrieve lead intelligence | Implemented |
| GET | `/api/leads/stats` | Operational counters | Implemented (not the full analytics module) |
| POST | `/api/outreach/generate` | Generate an outreach draft | Implemented |
| GET | `/api/outreach` | List outreach drafts | Implemented |
| GET | `/api/leads/{lead_id}/outreach` | Drafts for one lead | Implemented |

---

## 6. Not implemented in this scope

| Endpoint | Reason |
| --- | --- |
| `POST /api/leads/{id}/send` | No email sending workflow — drafts stay `draft` |
| `POST /api/leads/{id}/score/retrain` | No labelled outcome data yet |
| `GET /api/analytics/*` | Full sales analytics module is a later milestone |
| `POST /api/crm/sync` | CRM integration is a later milestone |
| `GET /api/conversations/*` | Conversation intelligence is a later milestone |
| `POST /api/auth/login` | Authentication/roles are not implemented in this window |
