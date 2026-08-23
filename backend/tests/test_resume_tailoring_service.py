import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, WorkExperience, CandidateSkill, Education
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.audit import AuditLog
from app.services.resume_tailoring_service import resume_tailoring_service


@pytest.mark.asyncio
async def test_resume_tailoring_service_execution(db_session: Session):
    # 1. Setup candidate profile
    profile = CandidateProfile(
        full_name="Morgan Reed",
        email="morgan.reed@example.com",
        location="Seattle, WA",
        headline="Senior AI Systems Engineer",
        summary="Building large-scale agentic AI workflows and inference pipelines.",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    exp = WorkExperience(
        profile_id=profile.id,
        company="Anthropic",
        position="Senior AI Engineer",
        start_date="2022-03",
        is_current=True,
        highlights=["Optimized local LLM inference on Apple Silicon and GPU clusters.", "Built tool-use framework."],
        skills_used=["Python", "FastAPI", "Ollama", "PyTorch"],
        is_verified=True,
    )
    edu = Education(
        profile_id=profile.id,
        institution="University of Washington",
        degree="B.S. Computer Science",
        start_date="2016",
        end_date="2020",
        is_verified=True,
    )
    skill = CandidateSkill(profile_id=profile.id, name="FastAPI", category="frameworks", proficiency="expert", is_verified=True)
    db_session.add_all([exp, edu, skill])
    db_session.commit()

    # 2. Setup Job listing and Analysis
    job = Job(
        title="Staff Autonomous Agent Engineer",
        company="OpenAI",
        location="San Francisco, CA",
        remote_type="remote",
        description_raw="Seeking a Staff Engineer to lead local model inference, multi-agent frameworks, and fast APIs.",
        source="unit_test",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=profile.id,
        fit_score=96.0,
        fit_level="high",
        matched_skills=["FastAPI", "Python", "Local LLM"],
        keywords=["Autonomous Agents", "Inference", "FastAPI"],
        status="completed",
    )
    db_session.add(analysis)
    db_session.commit()

    # 3. Mock Ollama response
    mock_tailored_json = {
        "tailored_summary": "Senior AI Engineer specializing in local LLM optimization and multi-agent orchestrations.",
        "highlighted_skills": ["FastAPI", "Python", "Ollama", "PyTorch"],
        "tailored_experience": [
            {
                "company": "Anthropic",
                "position": "Senior AI Engineer",
                "start_date": "2022-03",
                "end_date": None,
                "is_current": True,
                "tailored_highlights": [
                    "Optimized local LLM inference pipelines achieving sub-10ms response times.",
                    "Architected scalable tool-use and multi-agent framework.",
                ],
            }
        ],
        "cover_letter": "Dear OpenAI Hiring Team,\n\nI am thrilled to apply for the Staff Autonomous Agent Engineer role...\n\nSincerely,\nMorgan Reed",
        "diff_summary": "Emphasized local LLM inference speedups and multi-agent architectural accomplishments.",
    }

    with patch("app.services.llm.ollama_service.OllamaLLMService.generate_structured_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_tailored_json

        tailored = await resume_tailoring_service.tailor_application_materials(
            db=db_session,
            job_id=job.id,
            candidate_profile_id=profile.id,
            tone="confident",
        )

        assert tailored.id is not None
        assert tailored.job_id == job.id
        assert tailored.candidate_profile_id == profile.id
        assert "Senior AI Engineer" in tailored.tailored_summary
        assert "Dear OpenAI Hiring Team" in tailored.cover_letter
        assert len(tailored.highlighted_skills) == 4
        assert "# Morgan Reed" in tailored.markdown_content
        assert "## Professional Experience" in tailored.markdown_content
        assert tailored.status == "ready_for_review"

        # Verify Audit Log
        audit = db_session.query(AuditLog).filter(AuditLog.action == "RESUME_TAILORED").first()
        assert audit is not None
        assert f"job {job.id}" in audit.message
