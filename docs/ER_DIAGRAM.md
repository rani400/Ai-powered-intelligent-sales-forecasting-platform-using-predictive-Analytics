# Entity Relationship Diagram — SalesGenie AI

Database: PostgreSQL 14+ (production) / SQLite (local development and automated tests)
Dialect notes: `SERIAL PRIMARY KEY` is used on PostgreSQL and `INTEGER PRIMARY KEY AUTOINCREMENT`
on SQLite; the migration runner performs this substitution automatically.

---

## 1. Relationship overview

```
                    ┌──────────────────────────┐
                    │          users           │   (Module 5 - schema only)
                    │  user_id  PK             │
                    │  email     UQ           │
                    │  full_name              │
                    │  role                   │
                    └───────────┬──────────────┘
                                │ 1
                                │
                                │ N
                    ┌───────────┴──────────────┐
                    │    sales_interactions    │   (Module 5 - schema only)
                    │  interaction_id  PK       │
                    │  lead_id          FK ────┼──┐
                    │  user_id          FK ────┼──┘
                    │  interaction_type        │
                    │  subject / body          │
                    │  summary                 │
                    │  occurred_at             │
                    └──────────────────────────┘

  ┌──────────────────────────┐
  │         leads            │   Module 1 - IMPLEMENTED
  │  lead_id        PK       │
  │  company_name            │
  │  industry                │
  │  contact_name            │
  │  email                   │
  │  phone                   │
  │  lead_status             │
  │  company_size            │
  │  notes                   │
  │  source                  │
  │  is_active               │
  │  created_at / updated_at │
  └───────┬──────────┬───────┘
          │ 1        │ 1
          │          │
          │ N        │ N
┌─────────┴────────┐ │ ┌────────┴───────────────┐
│   lead_scores    │ │ │   company_insights     │   Module 2/4 - IMPLEMENTED
│ score_id   PK    │ │ │ insight_id     PK      │
│ lead_id    FK    │ │ │ lead_id        FK      │
│ score            │ │ │ company_name           │
│ band             │ │ │ industry               │
│ factors          │ │ │ summary                │
│ methodology      │ │ │ business_needs         │
│ created_at       │ │ │ opportunities          │
└──────────────────┘ │ │ key_insights           │
                     │ │ information_gaps       │
                     │ │ qualification_score    │
                     │ │ created_at             │
                     │ └────────────────────────┘
                     │
                     │ N
┌────────────────────┴───┐
│  outreach_campaigns    │   Module 3 - IMPLEMENTED
│  campaign_id     PK    │
│  lead_id         FK   │
│  email_subject         │
│  email_content         │
│  campaign_status       │
│  tone / email_length   │
│  communication_goal    │
│  provider / is_mock    │
│  created_at            │
└────────────────────────┘

┌──────────────────────────┐        ┌──────────────────────────┐
│      crm_sync_logs       │        │     sales_analytics       │
│  sync_id         PK      │        │  snapshot_id     PK       │
│  lead_id         FK      │        │  period_start             │
│  crm_system              │        │  period_end               │
│  entity_type             │        │  total_leads              │
│  sync_status             │        │  qualified_leads          │
│  records_synced          │        │  converted_leads          │
│  error_message           │        │  average_lead_score       │
│  created_at              │        │  conversion_rate          │
└──────────────────────────┘        │  created_at              │
        (Module 5 - schema only)     └──────────────────────────┘
                                          (Module 6 - schema only)
```

---

## 2. Table definitions

### 2.1 `leads` — implemented

| Column | Type | Null | Key | Default | Notes |
| --- | --- | --- | --- | --- | --- |
| `lead_id` | integer | no | PK | auto | Surrogate key |
| `company_name` | varchar(200) | no | | — | Trimmed, whitespace collapsed |
| `industry` | varchar(120) | yes | | — | Indexed |
| `contact_name` | varchar(120) | yes | | — | |
| `email` | varchar(320) | yes | | — | Indexed, stored lower-cased |
| `phone` | varchar(40) | yes | | — | Digits, spaces, `+ - ( )` allowed |
| `lead_status` | varchar(40) | no | | `'New'` | Indexed; one of New / Contacted / Qualified / Unqualified / Converted / Lost |
| `company_size` | varchar(50) | yes | | — | Bucket such as `51-200` |
| `notes` | text | yes | | — | Free-text engagement notes |
| `source` | varchar(40) | no | | `'manual'` | `manual` or `csv_import` |
| `is_active` | boolean | no | | `TRUE` | Soft-delete flag |
| `created_at` | timestamptz | no | | `CURRENT_TIMESTAMP` | |
| `updated_at` | timestamptz | no | | `CURRENT_TIMESTAMP` | Updated on write |

Indexes: `ix_leads_company_name`, `ix_leads_industry`, `ix_leads_email`, `ix_leads_lead_status`.

### 2.2 `lead_scores` — implemented

| Column | Type | Null | Key | Notes |
| --- | --- | --- | --- | --- |
| `score_id` | integer | no | PK | |
| `lead_id` | integer | no | FK → `leads.lead_id` | `ON DELETE CASCADE`, indexed |
| `score` | double precision | no | | 0–100 |
| `band` | varchar(20) | no | | Low / Medium / High |
| `factors` | varchar(2000) | no | | JSON list of scored factors |
| `methodology` | varchar(500) | no | | `rule_based_v1` |
| `created_at` | timestamptz | no | | Run timestamp |

**One-to-many:** a lead accumulates one score row per analysis run.

### 2.3 `company_insights` — implemented

| Column | Type | Null | Key | Notes |
| --- | --- | --- | --- | --- |
| `insight_id` | integer | no | PK | |
| `lead_id` | integer | no | FK → `leads.lead_id` | `ON DELETE CASCADE`, indexed |
| `company_name` | varchar(200) | no | | Snapshot of the company name |
| `industry` | varchar(120) | yes | | Snapshot of the industry |
| `summary` | text | no | | One-paragraph summary |
| `business_needs` | text | no | | JSON list |
| `opportunities` | text | no | | JSON list |
| `key_insights` | text | no | | JSON list |
| `information_gaps` | text | no | | JSON list |
| `qualification_score` | double precision | yes | | Score captured with the run |
| `created_at` | timestamptz | no | | Run timestamp |

**One-to-many:** a lead accumulates one insight row per analysis run.

### 2.4 `outreach_campaigns` — implemented

| Column | Type | Null | Key | Notes |
| --- | --- | --- | --- | --- |
| `campaign_id` | integer | no | PK | |
| `lead_id` | integer | no | FK → `leads.lead_id` | `ON DELETE CASCADE`, indexed |
| `email_subject` | varchar(300) | no | | Generated subject line |
| `email_content` | text | no | | Generated body |
| `campaign_status` | varchar(40) | no | | `draft` in this scope; indexed |
| `tone` | varchar(40) | yes | | `professional` / `friendly` |
| `email_length` | varchar(40) | yes | | `short` / `detailed` |
| `communication_goal` | varchar(60) | yes | | `product_introduction` / `meeting` / `follow_up` |
| `provider` | varchar(40) | no | | `mock` or the model name |
| `is_mock` | boolean | no | | `TRUE` when produced by the offline generator |
| `generation_latency_ms` | double precision | yes | | Provider round-trip time |
| `notes` | text | yes | | e.g. the mock-mode disclosure |
| `created_at` | timestamptz | no | | |

**One-to-many:** a lead accumulates one campaign row per generated draft.

### 2.5 Later-stage tables — schema only, no logic

| Table | Purpose | Status |
| --- | --- | --- |
| `users` | Platform users and roles | Schema only |
| `sales_interactions` | Calls, emails, meetings, notes per lead | Schema only |
| `crm_sync_logs` | CRM synchronisation audit trail | Schema only |
| `sales_analytics` | Pre-aggregated analytics snapshots | Schema only |

---

## 3. Referential integrity rules

| Rule | Enforcement |
| --- | --- |
| A score, insight or campaign cannot exist without a lead | `NOT NULL` FK with `ON DELETE CASCADE` |
| Deleting a lead removes its dependent rows | `ON DELETE CASCADE` on all three child tables |
| A deleted lead cannot be referenced by a soft-deleted interaction | FK is `ON DELETE SET NULL` |
| Duplicate active emails are rejected at the API layer | `DuplicateDetector` + `409` response |
| SQLite enforces the same rules in development and tests | `PRAGMA foreign_keys=ON` set on every connection |

## 4. Migration scripts

| Version | File | Contents |
| --- | --- | --- |
| 001 | `backend/migrations/001_initial_schema.sql` | `leads` table and indexes |
| 002 | `backend/migrations/002_intelligence_tables.sql` | `lead_scores`, `company_insights` |
| 003 | `backend/migrations/003_outreach_campaigns.sql` | `outreach_campaigns` |
| 004 | `backend/migrations/004_extended_tables.sql` | `users`, `sales_interactions`, `crm_sync_logs`, `sales_analytics` |

Applied versions are tracked in the `schema_migrations` table, so the runner never applies a
script twice.

```powershell
python backend/scripts/migrate.py --status
python backend/scripts/migrate.py
python backend/scripts/migrate.py --reset
```
