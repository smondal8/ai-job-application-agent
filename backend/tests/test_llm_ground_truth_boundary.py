from sqlalchemy.orm import Session
from app.models.candidate import (
    CandidateProfile,
    WorkExperience,
    Education,
    CandidateSkill,
    Project,
)
from app.services.profile_service import profile_service


def test_llm_ground_truth_boundary_strictly_filters_unverified_facts(db_session: Session):
    # 1. Create candidate profile (Verified)
    profile = CandidateProfile(
        full_name="Dr. Alan Turing",
        email="alan.turing@manchester.ac.uk",
        location="Manchester, UK",
        headline="Pioneer of Theoretical Computer Science",
        summary="Specialized in computational machines and cryptanalysis.",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()

    # 2. Add 2 experiences: 1 Verified, 1 Unverified (draft/untrusted import)
    exp_verified = WorkExperience(
        profile_id=profile.id,
        company="Bletchley Park",
        position="Chief Cryptanalyst",
        start_date="1939",
        end_date="1945",
        highlights=["Designed the Bombe machine to decipher Enigma."],
        skills_used=["Cryptanalysis", "Electromechanical Engineering"],
        is_verified=True,
    )
    exp_unverified = WorkExperience(
        profile_id=profile.id,
        company="Unverified Secret Lab",
        position="Temporal Research Intern",
        start_date="1950",
        end_date="1951",
        highlights=["Unverified draft claim that should NEVER reach the LLM."],
        is_verified=False,
    )
    db_session.add(exp_verified)
    db_session.add(exp_unverified)

    # 3. Add 2 skills: 1 Verified, 1 Unverified
    skill_verified = CandidateSkill(
        profile_id=profile.id,
        name="Mathematical Logic",
        category="foundations",
        proficiency="expert",
        is_verified=True,
    )
    skill_unverified = CandidateSkill(
        profile_id=profile.id,
        name="Quantum Teleportation (Unverified)",
        category="theoretical",
        proficiency="beginner",
        is_verified=False,
    )
    db_session.add(skill_verified)
    db_session.add(skill_unverified)

    # 4. Add 2 educations: 1 Verified, 1 Unverified
    edu_verified = Education(
        profile_id=profile.id,
        institution="King's College, Cambridge",
        degree="Ph.D. Mathematics",
        start_date="1931",
        end_date="1938",
        is_verified=True,
    )
    edu_unverified = Education(
        profile_id=profile.id,
        institution="Unverified University",
        degree="Honorary Degree",
        is_verified=False,
    )
    db_session.add(edu_verified)
    db_session.add(edu_unverified)

    # 5. Add 2 projects: 1 Verified, 1 Unverified
    proj_verified = Project(
        profile_id=profile.id,
        name="Turing Machine Formulation",
        description="Formalized the concept of algorithm and computation.",
        technologies=["Mathematical Logic"],
        is_verified=True,
    )
    proj_unverified = Project(
        profile_id=profile.id,
        name="Unverified Hallucination Project",
        description="Should never be visible to the LLM.",
        is_verified=False,
    )
    db_session.add(proj_verified)
    db_session.add(proj_unverified)
    db_session.commit()

    # Query the Authoritative Service Boundary
    gt_context = profile_service.get_verified_ground_truth_context(db_session, profile.id)

    # Verification Assertions:
    # 1. Experiences: ONLY the 1 verified experience is included
    assert len(gt_context["experiences"]) == 1
    assert gt_context["experiences"][0]["company"] == "Bletchley Park"
    assert "Unverified Secret Lab" not in str(gt_context["experiences"])

    # 2. Skills: ONLY the 1 verified skill is included
    assert len(gt_context["skills"]) == 1
    assert gt_context["skills"][0]["name"] == "Mathematical Logic"
    assert "Quantum Teleportation" not in str(gt_context["skills"])

    # 3. Educations: ONLY the 1 verified education is included
    assert len(gt_context["educations"]) == 1
    assert gt_context["educations"][0]["institution"] == "King's College, Cambridge"
    assert "Unverified University" not in str(gt_context["educations"])

    # 4. Projects: ONLY the 1 verified project is included
    assert len(gt_context["projects"]) == 1
    assert gt_context["projects"][0]["name"] == "Turing Machine Formulation"
    assert "Unverified Hallucination Project" not in str(gt_context["projects"])

    # 5. Check formatted markdown prompt context
    prompt_text = gt_context["formatted_llm_prompt_context"]
    assert "Bletchley Park" in prompt_text
    assert "Unverified Secret Lab" not in prompt_text
    assert "Unverified Hallucination Project" not in prompt_text
    assert "Quantum Teleportation" not in prompt_text


def test_llm_ground_truth_boundary_never_invents_missing_facts(db_session: Session):
    # Candidate profile with missing phone and website
    profile = CandidateProfile(
        full_name="Grace Hopper",
        email="grace.hopper@navy.mil",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()

    gt_context = profile_service.get_verified_ground_truth_context(db_session, profile.id)

    # Must be None/empty, never synthetic dummy values
    assert gt_context["candidate"]["phone"] is None
    assert gt_context["candidate"]["website"] is None
    assert gt_context["candidate"]["portfolio_url"] is None
    assert gt_context["experiences"] == []
    assert gt_context["skills"] == []
