import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, WorkExperience, CandidateSkill
from app.models.analysis import JobAnalysis
from app.models.audit import AuditLog
from app.services.jd_analysis_service import jd_analysis_service


@pytest.mark.asyncio
async def test_jd_analysis_service_execution(db_session: Session):
    # 1. Setup candidate profile with verified facts
    profile = CandidateProfile(
        full_name="Jordan Lee",
        email="jordan.lee@example.com",
        headline="Staff Distributed Systems Architect",
        summary="10+ years architecting high-throughput distributed databases.",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    exp = WorkExperience(
        profile_id=profile.id,
        company="Stripe",
        position="Staff Infrastructure Engineer",
        start_date="2020-01",
        is_current=True,
        highlights=["Scaled ledger streaming engine to 500k ops/sec."],
        skills_used=["Python", "Go", "Distributed Systems", "Raft"],
        is_verified=True,
    )
    db_session.add(exp)

    skill1 = CandidateSkill(profile_id=profile.id, name="Python", category="languages", proficiency="expert", is_verified=True)
    skill2 = CandidateSkill(profile_id=profile.id, name="Distributed Systems", category="general", proficiency="expert", is_verified=True)
    db_session.add_all([skill1, skill2])
    db_session.commit()

    # 2. Setup Job listing
    job = Job(
        title="Principal Distributed Systems Engineer",
        company="Netflix",
        location="Los Gatos, CA",
        remote_type="hybrid",
        description_raw="We are looking for a Principal Engineer with deep expertise in Python, Distributed Systems, and Kubernetes.",
        skills_raw=["Python", "Distributed Systems", "Kubernetes"],
        source="unit_test",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # 3. Mock Ollama semantic output
    # Deterministic match: 2 / 3 skills = 66.7%
    # Semantic match: 95.0%
    # Composite: (0.40 * 66.7) + (0.60 * 95.0) = 26.68 + 57.0 = 83.7%
    mock_analysis_payload = {
        "role_summary": "Architect distributed consensus and streaming engines for global video delivery.",
        "seniority_level_inferred": "staff",
        "key_responsibilities": ["Design high-throughput distributed pipelines", "Drive architectural decisions"],
        "required_qualifications": ["8+ years backend experience", "Experience with consensus algorithms"],
        "preferred_qualifications": ["Streaming video architecture"],
        "semantic_match_score": 95.0,
        "semantic_match_reasoning": "Jordan has direct hands-on experience scaling distributed streaming systems and matches all core requirements.",
        "matched_skills": ["Python", "Distributed Systems"],
        "missing_skills": ["Kubernetes"],
        "keywords": ["Distributed Systems", "Consensus", "High Throughput"],
        "red_flags": [],
        "recommendation": "strong_apply",
    }

    with patch("app.services.matching.semantic.SemanticMatcher.evaluate", new_callable=AsyncMock) as mock_sem:
        mock_sem.return_value = mock_analysis_payload

        analysis = await jd_analysis_service.analyze_job(
            db=db_session,
            job_id=job.id,
            candidate_profile_id=profile.id,
        )

        assert analysis.id is not None
        assert analysis.job_id == job.id
        assert analysis.candidate_profile_id == profile.id
        assert analysis.fit_score >= 80.0
        assert analysis.deterministic_score == 66.7
        assert analysis.semantic_score == 95.0
        assert analysis.fit_level == "high"
        assert analysis.recommendation == "strong_apply"
        assert "Jordan has direct" in analysis.summary
        assert "Python" in analysis.matched_skills
        assert "Kubernetes" in analysis.missing_skills
        assert analysis.status == "completed"

        # Verify Job status updated
        assert job.status == "analyzed"

        # Verify Audit Log
        audit = db_session.query(AuditLog).filter(AuditLog.action == "JOB_ANALYSIS_COMPLETED").first()
        assert audit is not None
        assert f"job {job.id}" in audit.message
