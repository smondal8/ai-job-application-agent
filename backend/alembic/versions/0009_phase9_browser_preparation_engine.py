"""phase 9 browser preparation engine

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-24 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_phase9_browser_preparation_engine'
down_revision: str = '0008_phase8_human_approval_state_machine'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create browser_preparation_runs table
    op.create_table(
        'browser_preparation_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('approval_id', sa.Integer(), nullable=True),
        sa.Column('approval_token', sa.String(length=128), nullable=False),
        sa.Column('portal_type', sa.String(length=100), nullable=False, server_default='generic'),
        sa.Column('portal_url', sa.String(length=1024), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='initialized'),
        sa.Column('fields_filled', sa.JSON(), nullable=True),
        sa.Column('unresolved_fields', sa.JSON(), nullable=True),
        sa.Column('resume_uploaded', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('resume_file_path', sa.String(length=1024), nullable=True),
        sa.Column('screenshot_path', sa.String(length=1024), nullable=True),
        sa.Column('final_submit_clicked', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('guard_triggered', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('captcha_detected', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('auth_required', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approval_id'], ['application_approvals.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_browser_preparation_runs_id'), 'browser_preparation_runs', ['id'], unique=False)
    op.create_index(op.f('ix_browser_preparation_runs_application_id'), 'browser_preparation_runs', ['application_id'], unique=False)
    op.create_index(op.f('ix_browser_preparation_runs_job_id'), 'browser_preparation_runs', ['job_id'], unique=False)
    op.create_index(op.f('ix_browser_preparation_runs_approval_id'), 'browser_preparation_runs', ['approval_id'], unique=False)
    op.create_index(op.f('ix_browser_preparation_runs_approval_token'), 'browser_preparation_runs', ['approval_token'], unique=False)
    op.create_index(op.f('ix_browser_preparation_runs_status'), 'browser_preparation_runs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_browser_preparation_runs_status'), table_name='browser_preparation_runs')
    op.drop_index(op.f('ix_browser_preparation_runs_approval_token'), table_name='browser_preparation_runs')
    op.drop_index(op.f('ix_browser_preparation_runs_approval_id'), table_name='browser_preparation_runs')
    op.drop_index(op.f('ix_browser_preparation_runs_job_id'), table_name='browser_preparation_runs')
    op.drop_index(op.f('ix_browser_preparation_runs_application_id'), table_name='browser_preparation_runs')
    op.drop_index(op.f('ix_browser_preparation_runs_id'), table_name='browser_preparation_runs')
    op.drop_table('browser_preparation_runs')
