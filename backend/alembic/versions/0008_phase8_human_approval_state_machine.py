"""0008_phase8_human_approval_state_machine

Revision ID: 0008_phase8_human_approval_state_machine
Revises: 0007_phase7_application_dashboard_and_review
Create Date: 2026-08-24 18:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008_phase8_human_approval_state_machine"
down_revision: Union[str, None] = "0007_phase7_application_dashboard_and_review"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update applications table
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("approval_token", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("invalidation_reason", sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f("ix_applications_approval_token"), ["approval_token"], unique=False)

    # 2. Create application_approvals table
    op.create_table(
        "application_approvals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("approved_job_hash", sa.String(length=64), nullable=False),
        sa.Column("candidate_profile_id", sa.Integer(), nullable=True),
        sa.Column("approved_candidate_hash", sa.String(length=64), nullable=False),
        sa.Column("tailored_resume_id", sa.Integer(), nullable=True),
        sa.Column("approved_resume_hash", sa.String(length=64), nullable=False),
        sa.Column("approved_answers_hash", sa.String(length=64), nullable=False),
        sa.Column("approval_token", sa.String(length=128), nullable=False),
        sa.Column("approver_id", sa.String(length=100), nullable=False),
        sa.Column("approver_notes", sa.Text(), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_profile_id"], ["candidate_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tailored_resume_id"], ["tailored_resumes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("application_approvals", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_application_approvals_application_id"), ["application_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_application_approvals_approval_token"), ["approval_token"], unique=True)
        batch_op.create_index(batch_op.f("ix_application_approvals_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_application_approvals_is_valid"), ["is_valid"], unique=False)
        batch_op.create_index(batch_op.f("ix_application_approvals_status"), ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("application_approvals")
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_applications_approval_token"))
        batch_op.drop_column("invalidation_reason")
        batch_op.drop_column("approved_at")
        batch_op.drop_column("approval_token")
