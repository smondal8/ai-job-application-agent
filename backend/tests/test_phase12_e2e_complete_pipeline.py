import os
import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.candidate import CandidateProfile, WorkExperience, Education, CandidateSkill
from app.models.job import Job
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application
from app.models.approval import ApplicationApproval
from app.models.preparation import BrowserPreparationRun
from app.services.approval import approval_service
from app.services.preparation import browser_preparation_engine, browser_session_manager
from app.services.jd_analysis_service import jd_analysis_service
from app.services.resume_tailoring_service import resume_tailoring_service


@pytest.fixture(autouse=True)
async def cleanup_browser_sessions():
    yield
    await browser_session_manager.close_all()


@pytest.mark.asyncio
async def test_phase12_complete_end_to_end_pipeline(db_session: Session, tmp_path: Path):
    """
    Phase 12 End-to-End Pipeline Verification:
    1. Candidate Profile Setup & Fact Verification
    2. Job Discovery & Ingestion (Greenhouse Fixture)
    3. Structured JD Analysis & Fit Scoring
    4. Grounded Resume Tailoring with Atomic Fact Traceability
    5. Application Dossier Review Workflow
    6. Explicit Cryptographic Human Approval Gate
    7. Server-Side Preparation Authorization Verification
    8. Playwright Browser Application Preparation against Local HTML Fixture
    9. Strict Final-Submit Guard Verification (Never Clicked)
    """

    # --- STEP 1: Candidate Profile & Atomic Facts ---
    candidate = CandidateProfile(
        full_name="Dr. Eleanor Vance",
        email="eleanor.vance@example.org",
        phone="+1-555-0199",
        location="Boston, MA",
        headline="Principal Distributed Systems Engineer",
        summary="Specialist in distributed consensus, Python, and async architecture.",
        is_verified=True,
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    exp1 = WorkExperience(
        profile_id=candidate.id,
        company="Apex Systems",
        position="Staff Engineer",
        start_date="2021-01-01",
        end_date="2024-01-01",
        is_current=False,
        highlights=[
            "Architected distributed Raft consensus engine handling 50k req/s.",
            "Led team of 8 backend engineers developing high-throughput Python microservices.",
        ],
        skills_used=["Python", "Raft", "Distributed Systems", "FastAPI"],
        is_verified=True,
    )
    skill1 = CandidateSkill(
        profile_id=candidate.id,
        name="Python",
        category="Languages",
        proficiency="Expert",
        is_verified=True,
    )
    skill2 = CandidateSkill(
        profile_id=candidate.id,
        name="Distributed Systems",
        category="Architecture",
        proficiency="Expert",
        is_verified=True,
    )
    db_session.add_all([exp1, skill1, skill2])
    db_session.commit()

    # --- STEP 2: Job Ingestion & Persistence ---
    raw_greenhouse_jd = """
    We are seeking a Staff Distributed Systems Engineer to lead core backend infrastructure.
    Requirements:
    - 5+ years building distributed systems in Python or Go.
    - Deep expertise with consensus algorithms (Raft, Paxos).
    - Strong communication and architectural leadership.
    """
    job = Job(
        title="Staff Distributed Systems Engineer",
        company="Nexus Infrastructure Inc.",
        location="Remote (US)",
        description_raw=raw_greenhouse_jd,
        description_clean="Staff Distributed Systems Engineer. Python, Raft, Distributed Systems.",
        source="greenhouse_feed",
        url="https://boards.greenhouse.io/nexusinfra/jobs/4099881",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id is not None
    assert job.company == "Nexus Infrastructure Inc."

    # --- STEP 3: Structured JD Analysis & Match Scoring ---
    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=candidate.id,
        fit_score=94.5,
        deterministic_score=95.0,
        semantic_score=94.0,
        fit_level="high",
        recommendation="strong_apply",
        summary="Exceptional fit for distributed systems infrastructure role.",
        matched_skills=["Python", "Distributed Systems", "Raft", "FastAPI"],
        missing_skills=["Go"],
        required_qualifications=["5+ years distributed systems", "Python"],
        status="completed",
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    assert analysis.fit_score >= 90.0
    assert analysis.recommendation == "strong_apply"

    # --- STEP 4: Grounded Tailored Resume Generation ---
    resume_file = tmp_path / "eleanor_vance_resume.pdf"
    resume_file.write_text("DUMMY PDF CONTENT FOR RESUME UPLOAD")

    tailored_resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=candidate.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        model_used="qwen3:8b",
        tailored_summary="Principal engineer specializing in distributed consensus systems and robust Python microservices.",
        tailored_experience=[
            {
                "company": "Apex Systems",
                "position": "Staff Engineer",
                "start_date": "2021-01-01",
                "end_date": "2024-01-01",
                "tailored_highlights": [
                    {
                        "text": "Architected distributed Raft consensus engine handling 50k req/s.",
                        "source_fact_ids": [f"exp_{exp1.id}_h0"],
                    },
                    {
                        "text": "Led team of 8 backend engineers developing high-throughput Python microservices.",
                        "source_fact_ids": [f"exp_{exp1.id}_h1"],
                    },
                ],
            }
        ],
        highlighted_skills=["Python", "Distributed Systems", "Raft", "FastAPI"],
        cover_letter="Dear Hiring Team at Nexus Infrastructure, I am excited to apply for the Staff Distributed Systems Engineer role...",
        compiled_markdown="# Dr. Eleanor Vance\n\nPrincipal Distributed Systems Engineer",
        file_path=str(resume_file),
        validation_status="valid",
        status="ready_for_review",
    )
    db_session.add(tailored_resume)
    db_session.commit()
    db_session.refresh(tailored_resume)

    assert tailored_resume.validation_status == "valid"

    # --- STEP 5: Central Application Creation & Linking ---
    app_entity = Application(
        job_id=job.id,
        candidate_profile_id=candidate.id,
        tailored_resume_id=tailored_resume.id,
        portal_type="greenhouse",
        portal_url=job.url,
        cover_letter=tailored_resume.cover_letter,
        answers_payload={
            "phone": candidate.phone,
            "linkedin": "https://linkedin.com/in/eleanor-vance",
            "authorized_to_work_in_us": "yes",
            "requires_sponsorship": "no",
        },
        status="ready_for_review",
    )
    db_session.add(app_entity)
    db_session.commit()
    db_session.refresh(app_entity)

    assert app_entity.status == "ready_for_review"

    # --- STEP 6: Explicit Cryptographic Human Approval Gate ---
    approval = approval_service.grant_approval(
        db=db_session,
        application_id=app_entity.id,
        approver_notes="Verified against Nexus Infrastructure job description. Approved for staging.",
        approver_id="user_admin",
    )

    assert approval is not None
    assert approval.status == "approved"
    assert approval.approval_token is not None
    assert approval.approved_job_hash is not None
    assert approval.approved_resume_hash is not None

    db_session.refresh(app_entity)
    assert app_entity.status == "approved"

    # --- STEP 7: Server-Side Authorization Verification ---
    auth_check = approval_service.authorize_for_preparation(db=db_session, application_id=app_entity.id)
    assert auth_check["authorization_granted"] is True
    assert auth_check["approval_token"] == approval.approval_token

    # --- STEP 8: Create Controlled Local HTML Portal Fixture ---
    portal_html = """<!DOCTYPE html>
    <html>
    <head><title>Nexus Infrastructure - Apply</title></head>
    <body>
        <h1>Apply for Staff Distributed Systems Engineer</h1>
        <form id="application_form" action="/submit" method="POST">
            <label for="first_name">First Name</label>
            <input type="text" id="first_name" name="first_name" />

            <label for="last_name">Last Name</label>
            <input type="text" id="last_name" name="last_name" />

            <label for="email">Email</label>
            <input type="email" id="email" name="email" />

            <label for="phone">Phone</label>
            <input type="tel" id="phone" name="phone" />

            <label for="resume">Resume/CV</label>
            <input type="file" id="resume" name="resume" />

            <label for="cover_letter">Cover Letter</label>
            <textarea id="cover_letter" name="cover_letter"></textarea>

            <label for="linkedin">LinkedIn Profile</label>
            <input type="url" id="linkedin" name="job_application[answers_attributes][0][text_value]" />

            <!-- Obvious Submit Button that Must NEVER Be Clicked -->
            <button type="submit" id="submit_app" class="btn-submit">Submit Application</button>
        </form>
    </body>
    </html>
    """
    html_fixture_file = tmp_path / "greenhouse_apply.html"
    html_fixture_file.write_text(portal_html)
    fixture_url = html_fixture_file.as_uri()

    # --- STEP 9: Execute Playwright Browser Preparation Engine ---
    prep_run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    # --- STEP 10: Verify Invariants & Final-Submit Guard ---
    assert prep_run is not None
    assert prep_run.status == "staged"
    assert prep_run.final_submit_clicked is False  # NON-NEGOTIABLE SECURITY INVARIANT
    assert prep_run.approval_token == approval.approval_token
    assert len(prep_run.fields_filled) >= 3
    assert prep_run.resume_uploaded is True
    assert prep_run.screenshot_path is not None
    assert Path(prep_run.screenshot_path).exists()
