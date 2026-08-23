from sqlalchemy.orm import Session
from app.services.profile_service import profile_service
from app.models.candidate import WorkExperience, CandidateSkill


def test_profile_lifecycle_and_verification(db_session: Session):
    # 1. Initialize primary profile
    profile = profile_service.get_or_create_primary_profile(db_session)
    assert profile.id is not None
    assert profile.is_verified is False

    # 2. Update profile details
    updated = profile_service.update_profile(
        db_session,
        profile.id,
        {
            "full_name": "Ada Lovelace",
            "email": "ada@lovelace.io",
            "headline": "First Computer Programmer",
        },
    )
    assert updated.full_name == "Ada Lovelace"
    assert updated.email == "ada@lovelace.io"

    # 3. Add Experience
    exp = profile_service.add_experience(
        db_session,
        profile.id,
        {
            "company": "Analytical Engine Co",
            "position": "Lead Algorithm Designer",
            "start_date": "1843",
            "highlights": ["Published the first computer algorithm."],
        },
    )
    assert exp.is_verified is False

    # 4. Add Skills in Bulk
    skills = profile_service.add_skills_bulk(
        db_session,
        profile.id,
        [
            {"name": "Algorithm Design", "category": "foundations"},
            {"name": "Mathematics", "category": "foundations"},
        ],
    )
    assert len(skills) == 2
    assert all(s.is_verified is False for s in skills)

    # 5. Verify Entire Profile
    verified_profile = profile_service.verify_profile(db_session, profile.id, verify_all_children=True)
    assert verified_profile.is_verified is True
    assert verified_profile.verified_at is not None

    # Check that children were verified
    reloaded_exp = db_session.query(WorkExperience).filter(WorkExperience.id == exp.id).first()
    assert reloaded_exp.is_verified is True

    reloaded_skills = db_session.query(CandidateSkill).filter(CandidateSkill.profile_id == profile.id).all()
    assert all(s.is_verified is True for s in reloaded_skills)


def test_apply_raw_import_to_profile_sets_untrusted_draft_state(db_session: Session):
    profile = profile_service.get_or_create_primary_profile(db_session)
    
    # 1. Ingest raw pasted resume text
    raw_text = """
    Linus Torvalds
    linus@kernel.org
    
    Experience
    Principal Architect - Linux Foundation
    - Created Linux Kernel and Git version control system.
    
    Skills
    C, Linux Kernel, Git, Distributed Systems
    """
    raw_import = profile_service.import_raw_resume_text(
        db_session, raw_text=raw_text, label="Linus CV", profile_id=profile.id
    )
    assert raw_import.status == "parsed"
    assert raw_import.file_hash is not None

    # 2. Transfer to profile
    updated_profile = profile_service.apply_raw_import_to_profile(
        db_session, import_id=raw_import.id, profile_id=profile.id
    )

    # 3. MUST be UNVERIFIED until user explicitly reviews
    assert updated_profile.is_verified is False
    assert updated_profile.full_name == "Linus Torvalds"
    assert updated_profile.email == "linus@kernel.org"

    # All experiences and skills must be untrusted/unverified
    assert len(updated_profile.experiences) >= 1
    assert any(exp.is_verified is False for exp in updated_profile.experiences)
    assert len(updated_profile.skills) >= 1
    assert all(s.is_verified is False for s in updated_profile.skills)
