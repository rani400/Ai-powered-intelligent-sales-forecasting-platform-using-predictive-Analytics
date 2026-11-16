"""Add CRM sync audit logs.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('crm_sync_logs',
        sa.Column('log_id', sa.Integer(), primary_key=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.lead_id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(30), nullable=False),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('remote_id', sa.String(120)),
        sa.Column('message', sa.String(250)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_crm_sync_logs_lead_id', 'crm_sync_logs', ['lead_id'])
    op.create_index('ix_crm_sync_logs_lead_created', 'crm_sync_logs', ['lead_id', 'created_at'])


def downgrade():
    op.drop_index('ix_crm_sync_logs_lead_created', table_name='crm_sync_logs')
    op.drop_index('ix_crm_sync_logs_lead_id', table_name='crm_sync_logs')
    op.drop_table('crm_sync_logs')
