"""0006_phase6_grounded_tailoring_and_traceability

Revision ID: 0006_phase6_grounded_tailoring_and_traceability
Revises: 0005_phase5_llm_analysis_and_tailoring
Create Date: 2026-08-23 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006_phase6_grounded_tailoring_and_traceability"
down_revision: Union[str, None] = "0005_phase5_llm_analysis_and_tailoring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend tailored_resumes table with traceability and deterministic compilation fields
    with op.batch_alter_table("tailored_resumes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("job_analysis_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("prompt_version", sa.String(length=50), server_default="v1.0.0", nullable=False))
        batch_op.add_column(sa.Column("cover_letter_paragraphs", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("compiled_markdown", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("compiled_text", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("compiled_html", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("traceability_matrix", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("validation_status", sa.String(length=50), server_default="valid", nullable=False))
        batch_op.add_column(sa.Column("validation_details", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("human_approved_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("human_approver_notes", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tailored_resumes_job_analysis_id",
            "job_analyses",
            ["job_analysis_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(batch_op.f("ix_tailored_resumes_job_analysis_id"), ["job_analysis_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tailored_resumes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tailored_resumes_job_analysis_id"))
        batch_op.drop_constraint("fk_tailored_resumes_job_analysis_id", type_="foreignkey")
        batch_op.drop_column("human_approver_notes")
        batch_op.drop_column("human_approved_at")
        batch_op.drop_column("validation_details")
        batch_op.drop_column("validation_status")
        batch_op.drop_column("traceability_matrix")
        batch_op.drop_column("compiled_html")
        batch_op.drop_column("compiled_text")
        batch_op.drop_column("compiled_markdown")
        batch_op.drop_column("cover_letter_paragraphs")
        batch_op.drop_column("prompt_version")
        batch_op.drop_column("job_analysis_id")
