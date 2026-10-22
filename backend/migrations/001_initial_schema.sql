-- 001 - Initial lead management schema
-- Placeholders are expanded by backend/scripts/migrate.py for the target engine:
--   {{PK}}     -> SERIAL PRIMARY KEY (PostgreSQL) | INTEGER PRIMARY KEY AUTOINCREMENT (SQLite)
--   {{FK_TYPE}}-> INTEGER (PostgreSQL)              | INTEGER (SQLite)
--   {{TS}}     -> TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP (PostgreSQL)
--                | DATETIME DEFAULT CURRENT_TIMESTAMP (SQLite)

CREATE TABLE IF NOT EXISTS leads (
    lead_id      {{PK}},
    company_name VARCHAR(200) NOT NULL,
    industry     VARCHAR(120),
    contact_name VARCHAR(120),
    email        VARCHAR(320),
    phone        VARCHAR(40),
    lead_status  VARCHAR(40) NOT NULL DEFAULT 'New',
    company_size VARCHAR(50),
    notes        TEXT,
    source       VARCHAR(40) NOT NULL DEFAULT 'manual',
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   {{TS}},
    updated_at   {{TS}}
);

CREATE INDEX IF NOT EXISTS ix_leads_company_name ON leads (company_name);
CREATE INDEX IF NOT EXISTS ix_leads_industry     ON leads (industry);
CREATE INDEX IF NOT EXISTS ix_leads_email        ON leads (email);
CREATE INDEX IF NOT EXISTS ix_leads_lead_status  ON leads (lead_status);
