"""phase 11 hardening and idempotency

Revision ID: 0010_phase11_hardening_and_idempotency
Revises: 0009_phase9_browser_preparation_engine
Create Date: 2026-08-24 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010_phase11_hardening_and_idempotency'
down_revision: str = '0009_phase9_browser_preparation_engine'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'idempotency_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='in_progress'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_idempotency_records_id'), 'idempotency_records', ['id'], unique=False)
    op.create_index(op.f('ix_idempotency_records_idempotency_key'), 'idempotency_records', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_idempotency_records_resource_type'), 'idempotency_records', ['resource_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_idempotency_records_resource_type'), table_name='idempotency_records')
    op.drop_index(op.f('ix_idempotency_records_idempotency_key'), table_name='idempotency_records')
    op.drop_index(op.f('ix_idempotency_records_id'), table_name='idempotency_records')
    op.drop_table('idempotency_records')
