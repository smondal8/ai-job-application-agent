"""Normalized job database and ingestion layer migration

Revision ID: 0003_normalized_job_database_and_ingestion
Revises: 0002_candidate_profile_and_master_resume
Create Date: 2026-08-23 20:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_normalized_job_database_and_ingestion"
down_revision: Union[str, None] = "0002_candidate_profile_and_master_resume"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. companies table
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("company_size", sa.String(length=50), nullable=True),
        sa.Column("careers_url", sa.String(length=1024), nullable=True),
        sa.Column("location_headquarters", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_companies_id"), "companies", ["id"], unique=False)
    op.create_index(op.f("ix_companies_normalized_name"), "companies", ["normalized_name"], unique=True)

    # 2. job_ingestion_batches table
    op.create_table(
        "job_ingestion_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("total_records", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("inserted_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("updated_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("error_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="completed", nullable=False),
        sa.Column("error_log", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_ingestion_batches_id"), "job_ingestion_batches", ["id"], unique=False)
    op.create_index(op.f("ix_job_ingestion_batches_batch_id"), "job_ingestion_batches", ["batch_id"], unique=True)
    op.create_index(op.f("ix_job_ingestion_batches_file_hash"), "job_ingestion_batches", ["file_hash"], unique=False)

    # 3. Add normalized columns to jobs table
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("batch_id", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("department", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("dedup_hash", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("normalized_company", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("normalized_title", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("normalized_location", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("workplace_type", sa.String(length=50), server_default="unspecified", nullable=True))
        batch_op.add_column(sa.Column("employment_type", sa.String(length=50), server_default="full_time", nullable=True))
        batch_op.add_column(sa.Column("seniority_level", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("experience_years_min", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("experience_years_max", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("skills_raw", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("benefits", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("metadata_extra", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False))
        batch_op.add_column(sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))

        batch_op.create_foreign_key("fk_jobs_company_id", "companies", ["company_id"], ["id"], ondelete="SET NULL")
        batch_op.create_foreign_key("fk_jobs_batch_id", "job_ingestion_batches", ["batch_id"], ["batch_id"], ondelete="SET NULL")
        batch_op.create_index("ix_jobs_dedup_hash", ["dedup_hash"], unique=False)
        batch_op.create_index("ix_jobs_normalized_company", ["normalized_company"], unique=False)
        batch_op.create_index("ix_jobs_normalized_title", ["normalized_title"], unique=False)
        batch_op.create_index("ix_jobs_normalized_location", ["normalized_location"], unique=False)
        batch_op.create_index("ix_jobs_is_active", ["is_active"], unique=False)
        batch_op.create_index("ix_jobs_company_id", ["company_id"], unique=False)
        batch_op.create_index("ix_jobs_batch_id", ["batch_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_index("ix_jobs_batch_id")
        batch_op.drop_index("ix_jobs_company_id")
        batch_op.drop_index("ix_jobs_is_active")
        batch_op.drop_index("ix_jobs_normalized_location")
        batch_op.drop_index("ix_jobs_normalized_title")
        batch_op.drop_index("ix_jobs_normalized_company")
        batch_op.drop_index("ix_jobs_dedup_hash")
        batch_op.drop_constraint("fk_jobs_batch_id", type_="foreignkey")
        batch_op.drop_constraint("fk_jobs_company_id", type_="foreignkey")
        batch_op.drop_column("last_seen_at")
        batch_op.drop_column("is_active")
        batch_op.drop_column("metadata_extra")
        batch_op.drop_column("benefits")
        batch_op.drop_column("skills_raw")
        batch_op.drop_column("experience_years_max")
        batch_op.drop_column("experience_years_min")
        batch_op.drop_column("seniority_level")
        batch_op.drop_column("employment_type")
        batch_op.drop_column("workplace_type")
        batch_op.drop_column("normalized_location")
        batch_op.drop_column("normalized_title")
        batch_op.drop_column("normalized_company")
        batch_op.drop_column("dedup_hash")
        batch_op.drop_column("department")
        batch_op.drop_column("batch_id")
        batch_op.drop_column("company_id")

    op.drop_table("job_ingestion_batches")
    op.drop_table("companies")
