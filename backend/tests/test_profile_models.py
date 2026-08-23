from sqlalchemy.orm import Session
from app.models.candidate import (
    CandidateProfile,
    WorkExperience,
    Education,
    CandidateSkill,
    Project,
    RawResumeImport,
)


def test_candidate_profile_model_crud(db_session: Session):
    profile = CandidateProfile(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+1 (555) 123-4567",
        location="New York, NY",
        headline="Principal Software Engineer",
        summary="Experienced distributed systems architect.",
        is_verified=False,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    assert profile.id is not None
    assert profile.full_name == "Jane Doe"
    assert profile.is_verified is False
    assert profile.created_at is not None
    assert profile.updated_at is not None


def test_candidate_profile_relationships_and_cascade(db_session: Session):
    profile = CandidateProfile(
        full_name="John Smith",
        email="john.smith@example.com",
        is_verified=False,
    )
    db_session.add(profile)
    db_session.commit()

    # 1. Experience
    exp = WorkExperience(
        profile_id=profile.id,
        company="OpenAI",
        position="AI Engineer",
        start_date="2023-01",
        is_current=True,
        highlights=["Implemented high-throughput model serving."],
        skills_used=["Python", "Triton", "FastAPI"],
        is_verified=False,
    )
    db_session.add(exp)

    # 2. Education
    edu = Education(
        profile_id=profile.id,
        institution="MIT",
        degree="B.S. EECS",
        start_date="2018",
        end_date="2022",
        is_verified=False,
    )
    db_session.add(edu)

    # 3. Skill
    skill = CandidateSkill(
        profile_id=profile.id,
        name="PyTorch",
        category="frameworks",
        proficiency="expert",
        is_verified=False,
    )
    db_session.add(skill)

    # 4. Project
    proj = Project(
        profile_id=profile.id,
        name="Distributed Agent Orchestrator",
        description="Scalable task engine.",
        technologies=["Python", "Redis", "Docker"],
        is_verified=False,
    )
    db_session.add(proj)

    # 5. Raw Import
    raw_imp = RawResumeImport(
        profile_id=profile.id,
        filename="resume_v1.pdf",
        file_path="./data/storage/resumes/abc_resume_v1.pdf",
        file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_size_bytes=1024,
        mime_type="application/pdf",
        status="parsed",
    )
    db_session.add(raw_imp)
    db_session.commit()

    # Verify query
    saved_profile = db_session.query(CandidateProfile).filter(CandidateProfile.id == profile.id).first()
    assert saved_profile is not None
    assert len(saved_profile.experiences) == 1
    assert len(saved_profile.educations) == 1
    assert len(saved_profile.skills) == 1
    assert len(saved_profile.projects) == 1
    assert len(saved_profile.raw_imports) == 1

    # Cascade delete check
    db_session.delete(saved_profile)
    db_session.commit()

    assert db_session.query(WorkExperience).filter(WorkExperience.profile_id == profile.id).count() == 0
    assert db_session.query(Education).filter(Education.profile_id == profile.id).count() == 0
    assert db_session.query(CandidateSkill).filter(CandidateSkill.profile_id == profile.id).count() == 0
    assert db_session.query(Project).filter(Project.profile_id == profile.id).count() == 0
