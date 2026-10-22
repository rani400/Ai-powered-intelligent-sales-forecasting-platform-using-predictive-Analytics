-- 003 - Outreach campaigns table (Module 3: AI outreach generation and draft storage)

CREATE TABLE IF NOT EXISTS outreach_campaigns (
    campaign_id          {{PK}},
    lead_id              {{FK_TYPE}} NOT NULL REFERENCES leads (lead_id) ON DELETE CASCADE,
    email_subject        VARCHAR(300) NOT NULL,
    email_content        TEXT NOT NULL,
    campaign_status      VARCHAR(40) NOT NULL DEFAULT 'draft',
    tone                 VARCHAR(40),
    email_length         VARCHAR(40),
    communication_goal   VARCHAR(60),
    provider             VARCHAR(40) NOT NULL DEFAULT 'mock',
    is_mock              BOOLEAN NOT NULL DEFAULT TRUE,
    generation_latency_ms DOUBLE PRECISION,
    notes                TEXT,
    created_at           {{TS}}
);

CREATE INDEX IF NOT EXISTS ix_outreach_campaigns_lead_id         ON outreach_campaigns (lead_id);
CREATE INDEX IF NOT EXISTS ix_outreach_campaigns_campaign_status ON outreach_campaigns (campaign_status);
