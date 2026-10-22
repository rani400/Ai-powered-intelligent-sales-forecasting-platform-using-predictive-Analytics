-- 004 - Tables reserved for the later milestones (Module 5 and Module 6)
-- Schema only. No services or endpoints use these tables in the current scope.

CREATE TABLE IF NOT EXISTS users (
    user_id    {{PK}},
    full_name  VARCHAR(150) NOT NULL,
    email      VARCHAR(320) NOT NULL UNIQUE,
    role       VARCHAR(40) NOT NULL DEFAULT 'sales_rep',
    is_active  BOOLEAN NOT NULL DEFAULT TRUE,
    created_at {{TS}}
);

CREATE TABLE IF NOT EXISTS sales_interactions (
    interaction_id   {{PK}},
    lead_id          {{FK_TYPE}} NOT NULL REFERENCES leads (lead_id) ON DELETE CASCADE,
    user_id          {{FK_TYPE}} REFERENCES users (user_id) ON DELETE SET NULL,
    interaction_type VARCHAR(40) NOT NULL DEFAULT 'note',
    subject          VARCHAR(300),
    body             TEXT,
    summary          TEXT,
    occurred_at      {{TS}}
);

CREATE INDEX IF NOT EXISTS ix_sales_interactions_lead_id ON sales_interactions (lead_id);

CREATE TABLE IF NOT EXISTS crm_sync_logs (
    sync_id       {{PK}},
    lead_id       {{FK_TYPE}} REFERENCES leads (lead_id) ON DELETE SET NULL,
    crm_system    VARCHAR(60) NOT NULL,
    entity_type   VARCHAR(60) NOT NULL DEFAULT 'lead',
    sync_status   VARCHAR(40) NOT NULL DEFAULT 'pending',
    records_synced INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at    {{TS}}
);

CREATE INDEX IF NOT EXISTS ix_crm_sync_logs_lead_id ON crm_sync_logs (lead_id);

CREATE TABLE IF NOT EXISTS sales_analytics (
    snapshot_id        {{PK}},
    period_start       {{TS}},
    period_end         {{TS}},
    total_leads        INTEGER NOT NULL DEFAULT 0,
    qualified_leads    INTEGER NOT NULL DEFAULT 0,
    converted_leads    INTEGER NOT NULL DEFAULT 0,
    average_lead_score DOUBLE PRECISION,
    conversion_rate    DOUBLE PRECISION,
    notes              TEXT,
    created_at         {{TS}}
);
