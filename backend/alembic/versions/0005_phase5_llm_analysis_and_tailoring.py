"""0005_phase5_llm_analysis_and_tailoring

Revision ID: 0005_phase5_llm_analysis_and_tailoring
Revises: 0004_job_discovery_framework
Create Date: 2026-08-23 21:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_phase5_llm_analysis_and_tailoring"
down_revision: Union[str, None] = "0004_job_discovery_framework"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend job_analyses table
    with op.batch_alter_table("job_analyses", schema=None) as batch_op:
        batch_op.add_column(sa.Column("candidate_profile_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("role_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("key_responsibilities", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("model_used", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("raw_llm_response", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_job_analyses_candidate_profile_id",
            "candidate_profiles",
            ["candidate_profile_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(batch_op.f("ix_job_analyses_candidate_profile_id"), ["candidate_profile_id"], unique=False)

    # 2. Extend tailored_resumes table
    with op.batch_alter_table("tailored_resumes", schema=None) as batch_op:
        batch_op.alter_column("base_resume_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("candidate_profile_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cover_letter", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("markdown_content", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("status", sa.String(length=50), server_default="generated", nullable=False))
        batch_op.add_column(sa.Column("model_used", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("generation_metadata", sa.JSON(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tailored_resumes_candidate_profile_id",
            "candidate_profiles",
            ["candidate_profile_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(batch_op.f("ix_tailored_resumes_candidate_profile_id"), ["candidate_profile_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tailored_resumes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tailored_resumes_candidate_profile_id"))
        batch_op.drop_constraint("fk_tailored_resumes_candidate_profile_id", type_="foreignkey")
        batch_op.drop_column("generation_metadata")
        batch_op.drop_column("model_used")
        batch_op.drop_column("status")
        batch_op.drop_column("markdown_content")
        batch_op.drop_column("cover_letter")
        batch_op.drop_column("candidate_profile_id")
        batch_op.alter_column("base_resume_id", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("job_analyses", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_job_analyses_candidate_profile_id"))
        batch_op.drop_constraint("fk_job_analyses_candidate_profile_id", type_="foreignkey")
        batch_op.drop_column("raw_llm_response")
        batch_op.drop_column("model_used")
        batch_op.drop_column("key_responsibilities")
        batch_op.drop_column("role_summary")
        batch_op.drop_column("candidate_profile_id")
