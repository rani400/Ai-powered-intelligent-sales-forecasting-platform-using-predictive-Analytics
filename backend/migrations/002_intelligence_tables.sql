-- 002 - Lead intelligence tables (Module 2 and Module 4 baseline)
-- A lead can have many lead_scores rows and many company_insights rows (one-to-many).

CREATE TABLE IF NOT EXISTS lead_scores (
    score_id    {{PK}},
    lead_id     {{FK_TYPE}} NOT NULL REFERENCES leads (lead_id) ON DELETE CASCADE,
    score       DOUBLE PRECISION NOT NULL,
    band        VARCHAR(20) NOT NULL,
    factors     VARCHAR(2000) NOT NULL DEFAULT '[]',
    methodology VARCHAR(500) NOT NULL DEFAULT 'rule_based_v1',
    created_at  {{TS}}
);

CREATE INDEX IF NOT EXISTS ix_lead_scores_lead_id ON lead_scores (lead_id);

CREATE TABLE IF NOT EXISTS company_insights (
    insight_id          {{PK}},
    lead_id             {{FK_TYPE}} NOT NULL REFERENCES leads (lead_id) ON DELETE CASCADE,
    company_name        VARCHAR(200) NOT NULL,
    industry            VARCHAR(120),
    summary             TEXT NOT NULL,
    business_needs      TEXT NOT NULL DEFAULT '[]',
    opportunities       TEXT NOT NULL DEFAULT '[]',
    key_insights        TEXT NOT NULL DEFAULT '[]',
    information_gaps    TEXT NOT NULL DEFAULT '[]',
    qualification_score DOUBLE PRECISION,
    created_at          {{TS}}
);

CREATE INDEX IF NOT EXISTS ix_company_insights_lead_id ON company_insights (lead_id);
