"""Initial four-module database schema
Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('leads',
        sa.Column('lead_id', sa.Integer(), primary_key=True),
        sa.Column('company_name', sa.String(200), nullable=False),
        sa.Column('industry', sa.String(100)),
        sa.Column('contact_name', sa.String(150)),
        sa.Column('email', sa.String(254)),
        sa.Column('phone', sa.String(40)),
        sa.Column('lead_status', sa.String(30), nullable=False),
        sa.Column('company_size', sa.String(30)),
        sa.Column('engagement_score', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('source', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('engagement_score >= 0 AND engagement_score <= 100', name='ck_lead_engagement'))
    for col in ('company_name', 'industry', 'email', 'lead_status'):
        op.create_index('ix_leads_' + col, 'leads', [col], unique=(col == 'email'))
    op.create_index('ix_leads_company_contact', 'leads', ['company_name', 'contact_name'])

    op.create_table('company_insights',
        sa.Column('insight_id', sa.Integer(), primary_key=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.lead_id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_summary', sa.Text(), nullable=False),
        sa.Column('industry_context', sa.Text(), nullable=False),
        sa.Column('potential_needs', sa.JSON(), nullable=False),
        sa.Column('potential_opportunities', sa.JSON(), nullable=False),
        sa.Column('observations', sa.JSON(), nullable=False),
        sa.Column('information_gaps', sa.JSON(), nullable=False),
        sa.Column('qualification_score', sa.Float(), nullable=False),
        sa.Column('qualification_band', sa.String(30), nullable=False),
        sa.Column('contributing_factors', sa.JSON(), nullable=False),
        sa.Column('methodology', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_company_insights_lead_id', 'company_insights', ['lead_id'])
    op.create_index('ix_insight_lead_date', 'company_insights', ['lead_id', 'created_at'])

    op.create_table('lead_scores',
        sa.Column('score_id', sa.Integer(), primary_key=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.lead_id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('priority_band', sa.String(30), nullable=False),
        sa.Column('factors', sa.JSON(), nullable=False),
        sa.Column('conversion_probability', sa.Float()),
        sa.Column('prediction_mode', sa.String(30), nullable=False),
        sa.Column('model_version', sa.String(100), nullable=False),
        sa.Column('recommended_action', sa.String(200), nullable=False),
        sa.Column('recommendation_reason', sa.Text(), nullable=False),
        sa.Column('recommendation_priority', sa.String(30), nullable=False),
        sa.Column('supporting_factors', sa.JSON(), nullable=False),
        sa.Column('suggested_outreach_goal', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_lead_scores_lead_id', 'lead_scores', ['lead_id'])
    op.create_index('ix_score_lead_date', 'lead_scores', ['lead_id', 'created_at'])

    op.create_table('outreach_campaigns',
        sa.Column('campaign_id', sa.Integer(), primary_key=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.lead_id', ondelete='CASCADE'), nullable=False),
        sa.Column('email_subject', sa.String(300), nullable=False),
        sa.Column('email_content', sa.Text(), nullable=False),
        sa.Column('tone', sa.String(30), nullable=False),
        sa.Column('communication_goal', sa.String(40), nullable=False),
        sa.Column('email_length', sa.String(20), nullable=False),
        sa.Column('provider', sa.String(40), nullable=False),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('campaign_status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_outreach_campaigns_lead_id', 'outreach_campaigns', ['lead_id'])
    op.create_index('ix_campaign_lead_date', 'outreach_campaigns', ['lead_id', 'created_at'])


def downgrade():
    for table in ('outreach_campaigns', 'lead_scores', 'company_insights', 'leads'):
        op.drop_table(table)
