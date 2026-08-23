"""Job discovery framework and orchestration migration

Revision ID: 0004_job_discovery_framework
Revises: 0003_normalized_job_database_and_ingestion
Create Date: 2026-08-23 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_job_discovery_framework"
down_revision: Union[str, None] = "0003_normalized_job_database_and_ingestion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. job_discovery_runs table
    op.create_table(
        "job_discovery_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("total_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="running"),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("adapter_logs", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_discovery_runs_id", "job_discovery_runs", ["id"], unique=False)
    op.create_index("ix_job_discovery_runs_run_id", "job_discovery_runs", ["run_id"], unique=True)
    op.create_index("ix_job_discovery_runs_status", "job_discovery_runs", ["status"], unique=False)

    # 2. job_search_profiles table
    op.create_table(
        "job_search_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("auto_run_interval_hours", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_job_search_profiles_id", "job_search_profiles", ["id"], unique=False)
    op.create_index("ix_job_search_profiles_is_active", "job_search_profiles", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_search_profiles_is_active", table_name="job_search_profiles")
    op.drop_index("ix_job_search_profiles_id", table_name="job_search_profiles")
    op.drop_table("job_search_profiles")

    op.drop_index("ix_job_discovery_runs_status", table_name="job_discovery_runs")
    op.drop_index("ix_job_discovery_runs_run_id", table_name="job_discovery_runs")
    op.drop_index("ix_job_discovery_runs_id", table_name="job_discovery_runs")
    op.drop_table("job_discovery_runs")
