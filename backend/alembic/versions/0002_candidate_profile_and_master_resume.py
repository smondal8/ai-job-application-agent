"""Candidate profile and master resume subsystem migration

Revision ID: 0002_candidate_profile_and_master_resume
Revises: 0001_initial_schema
Create Date: 2026-08-23 19:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_candidate_profile_and_master_resume"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. candidate_profiles table
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("linkedin_url", sa.String(length=512), nullable=True),
        sa.Column("github_url", sa.String(length=512), nullable=True),
        sa.Column("portfolio_url", sa.String(length=512), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_candidate_profiles_id"), "candidate_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_candidate_profiles_full_name"), "candidate_profiles", ["full_name"], unique=False)
    op.create_index(op.f("ix_candidate_profiles_email"), "candidate_profiles", ["email"], unique=False)
    op.create_index(op.f("ix_candidate_profiles_is_verified"), "candidate_profiles", ["is_verified"], unique=False)

    # 2. work_experiences table
    op.create_table(
        "work_experiences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("position", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.String(length=50), nullable=False),
        sa.Column("end_date", sa.String(length=50), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("highlights", sa.JSON(), nullable=True),
        sa.Column("skills_used", sa.JSON(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_work_experiences_id"), "work_experiences", ["id"], unique=False)
    op.create_index(op.f("ix_work_experiences_profile_id"), "work_experiences", ["profile_id"], unique=False)
    op.create_index(op.f("ix_work_experiences_is_verified"), "work_experiences", ["is_verified"], unique=False)

    # 3. educations table
    op.create_table(
        "educations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("institution", sa.String(length=255), nullable=False),
        sa.Column("degree", sa.String(length=255), nullable=False),
        sa.Column("field_of_study", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.String(length=50), nullable=True),
        sa.Column("end_date", sa.String(length=50), nullable=True),
        sa.Column("gpa", sa.String(length=50), nullable=True),
        sa.Column("highlights", sa.JSON(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_educations_id"), "educations", ["id"], unique=False)
    op.create_index(op.f("ix_educations_profile_id"), "educations", ["profile_id"], unique=False)
    op.create_index(op.f("ix_educations_is_verified"), "educations", ["is_verified"], unique=False)

    # 4. candidate_skills table
    op.create_table(
        "candidate_skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), server_default="general", nullable=False),
        sa.Column("proficiency", sa.String(length=50), server_default="intermediate", nullable=False),
        sa.Column("years_of_experience", sa.Float(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_candidate_skills_id"), "candidate_skills", ["id"], unique=False)
    op.create_index(op.f("ix_candidate_skills_profile_id"), "candidate_skills", ["profile_id"], unique=False)
    op.create_index(op.f("ix_candidate_skills_name"), "candidate_skills", ["name"], unique=False)
    op.create_index(op.f("ix_candidate_skills_is_verified"), "candidate_skills", ["is_verified"], unique=False)

    # 5. projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=512), nullable=True),
        sa.Column("highlights", sa.JSON(), nullable=True),
        sa.Column("technologies", sa.JSON(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_id"), "projects", ["id"], unique=False)
    op.create_index(op.f("ix_projects_profile_id"), "projects", ["profile_id"], unique=False)
    op.create_index(op.f("ix_projects_is_verified"), "projects", ["is_verified"], unique=False)

    # 6. raw_resume_imports table
    op.create_table(
        "raw_resume_imports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_data", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="uploaded", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_raw_resume_imports_id"), "raw_resume_imports", ["id"], unique=False)
    op.create_index(op.f("ix_raw_resume_imports_profile_id"), "raw_resume_imports", ["profile_id"], unique=False)
    op.create_index(op.f("ix_raw_resume_imports_file_hash"), "raw_resume_imports", ["file_hash"], unique=False)


def downgrade() -> None:
    op.drop_table("raw_resume_imports")
    op.drop_table("projects")
    op.drop_table("candidate_skills")
    op.drop_table("educations")
    op.drop_table("work_experiences")
    op.drop_table("candidate_profiles")
