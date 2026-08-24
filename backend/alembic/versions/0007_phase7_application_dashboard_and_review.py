"""0007_phase7_application_dashboard_and_review

Revision ID: 0007_phase7_application_dashboard_and_review
Revises: 0006_phase6_grounded_tailoring_and_traceability
Create Date: 2026-08-24 18:27:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0007_phase7_application_dashboard_and_review"
down_revision: Union[str, None] = "0006_phase6_grounded_tailoring_and_traceability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("candidate_profile_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reviewer_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key(
            "fk_applications_candidate_profile_id",
            "candidate_profiles",
            ["candidate_profile_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(batch_op.f("ix_applications_candidate_profile_id"), ["candidate_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_applications_tailored_resume_id"), ["tailored_resume_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_applications_tailored_resume_id"))
        batch_op.drop_index(batch_op.f("ix_applications_candidate_profile_id"))
        batch_op.drop_constraint("fk_applications_candidate_profile_id", type_="foreignkey")
        batch_op.drop_column("applied_at")
        batch_op.drop_column("reviewer_notes")
        batch_op.drop_column("candidate_profile_id")
