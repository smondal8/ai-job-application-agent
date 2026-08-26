import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, WorkExperience, CandidateSkill, Education
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.audit import AuditLog
from app.services.tailoring.tailoring_service import resume_tailoring_service


@pytest.mark.asyncio
async def test_resume_tailoring_service_grounded_execution(db_session: Session):
    # 1. Setup candidate profile with verified facts
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
    skill1 = CandidateSkill(profile_id=profile.id, name="FastAPI", category="frameworks", proficiency="expert", is_verified=True)
    skill2 = CandidateSkill(profile_id=profile.id, name="Python", category="languages", proficiency="expert", is_verified=True)
    db_session.add_all([exp, edu, skill1, skill2])
    db_session.commit()
    db_session.refresh(exp)

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

    # 3. Mock Ollama response with explicit source_fact_ids
    mock_tailored_json = {
        "tailored_summary": {
            "text": "Senior AI Engineer specializing in local LLM optimization and multi-agent systems.",
            "source_fact_ids": [f"profile:{profile.id}:headline", f"exp:{exp.id}"],
        },
        "highlighted_skills": [
            {"name": "FastAPI", "source_fact_ids": [f"skill:{skill1.id}"]},
            {"name": "Python", "source_fact_ids": [f"skill:{skill2.id}"]},
        ],
        "tailored_experience": [
            {
                "company": "Anthropic",
                "position": "Senior AI Engineer",
                "start_date": "2022-03",
                "end_date": None,
                "is_current": True,
                "tailored_highlights": [
                    {
                        "text": "Optimized local LLM inference pipelines achieving sub-10ms response times on Apple Silicon.",
                        "source_fact_ids": [f"exp:{exp.id}:h0"],
                    },
                    {
                        "text": "Architected scalable tool-use and multi-agent framework.",
                        "source_fact_ids": [f"exp:{exp.id}:h1"],
                    },
                ],
            }
        ],
        "cover_letter_paragraphs": [
            {
                "paragraph_type": "opening",
                "text": "I am eager to apply for the Staff Autonomous Agent Engineer role at OpenAI.",
                "source_fact_ids": [f"profile:{profile.id}:headline"],
            },
            {
                "paragraph_type": "body_experience",
                "text": "At Anthropic, I optimized local LLM inference and tool use frameworks.",
                "source_fact_ids": [f"exp:{exp.id}:h0", f"exp:{exp.id}:h1"],
            },
        ],
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
        assert tailored.prompt_version == "v1.0.0"
        assert tailored.validation_status == "valid"
        assert tailored.validation_details["traceability_score"] == 100.0
        assert "Senior AI Engineer" in tailored.tailored_summary
        assert "Dear OpenAI Hiring Team" in tailored.cover_letter
        assert len(tailored.highlighted_skills) == 2
        assert "# Morgan Reed" in tailored.compiled_markdown
        assert "## Professional Experience" in tailored.compiled_markdown
        assert tailored.compiled_text is not None
        assert tailored.compiled_html is not None
        assert tailored.status == "ready_for_review"

        # Verify Audit Log
        audit = db_session.query(AuditLog).filter(AuditLog.action == "RESUME_TAILORED_GROUNDED").first()
        assert audit is not None
        assert f"job {job.id}" in audit.message


@pytest.mark.asyncio
async def test_resume_tailoring_service_fallback_on_empty_or_error_llm(db_session: Session):
    """Ensure that if LLM returns an error dictionary or empty output, the candidate's complete verified facts are preserved."""
    profile = CandidateProfile(
        full_name="Alex Chen",
        email="alex.chen@example.com",
        location="Austin, TX",
        headline="Staff Platform Engineer | Go, Kubernetes, Kafka",
        summary="12+ years building cloud-native platform infrastructure.",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    exp1 = WorkExperience(
        profile_id=profile.id,
        company="Datadog",
        position="Senior Platform Engineer",
        start_date="2021-01",
        is_current=True,
        highlights=[
            "Scaled metrics aggregation pipeline handling 2M events/sec.",
            "Maintained zero-downtime Kubernetes control planes.",
        ],
        skills_used=["Go", "Kubernetes", "Kafka"],
        is_verified=True,
    )
    exp2 = WorkExperience(
        profile_id=profile.id,
        company="Uber",
        position="Software Engineer II",
        start_date="2018-05",
        end_date="2020-12",
        is_current=False,
        description="Built low-latency gRPC services for driver location tracking.\nOptimized Cassandra queries reducing p99 latency by 25%.",
        is_verified=True,
    )
    edu = Education(
        profile_id=profile.id,
        institution="UT Austin",
        degree="B.S.",
        field_of_study="Electrical and Computer Engineering",
        start_date="2014",
        end_date="2018",
        is_verified=True,
    )
    skill1 = CandidateSkill(profile_id=profile.id, name="Go", category="languages", is_verified=True)
    skill2 = CandidateSkill(profile_id=profile.id, name="Kubernetes", category="cloud_devops", is_verified=True)
    db_session.add_all([exp1, exp2, edu, skill1, skill2])
    db_session.commit()

    job = Job(
        title="Lead Infrastructure Engineer",
        company="Stripe",
        location="Remote",
        remote_type="remote",
        description_raw="Looking for Lead Infrastructure Engineer with Go, Kubernetes, and high-throughput streaming systems.",
        source="unit_test",
    )
    db_session.add(job)
    db_session.commit()

    # Simulate LLM returning an error payload
    with patch("app.services.llm.ollama_service.OllamaLLMService.generate_structured_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {"error": "Invalid JSON: Expecting value"}

        tailored = await resume_tailoring_service.tailor_application_materials(
            db=db_session,
            job_id=job.id,
            candidate_profile_id=profile.id,
        )

        assert tailored.id is not None
        # Summary must NOT be empty
        assert len(tailored.tailored_summary) > 0
        assert "Staff Platform Engineer" in tailored.tailored_summary or "12+ years" in tailored.tailored_summary

        # Experience must contain BOTH work experiences
        assert len(tailored.tailored_experience) == 2
        exp_companies = [e["company"] for e in tailored.tailored_experience]
        assert "Datadog" in exp_companies
        assert "Uber" in exp_companies

        # Skills must be populated
        assert len(tailored.highlighted_skills) >= 2
        assert "Go" in tailored.highlighted_skills or "Kubernetes" in tailored.highlighted_skills

        # Cover letter must be complete
        assert "Stripe" in tailored.cover_letter
        assert "Lead Infrastructure Engineer" in tailored.cover_letter

        # ATS Markdown must contain all sections
        assert "# Alex Chen" in tailored.compiled_markdown
        assert "## Professional Summary" in tailored.compiled_markdown
        assert "## Core Competencies & Technical Skills" in tailored.compiled_markdown
        assert "## Professional Experience" in tailored.compiled_markdown
        assert "### Senior Platform Engineer | **Datadog**" in tailored.compiled_markdown
        assert "- Scaled metrics aggregation pipeline handling 2M events/sec." in tailored.compiled_markdown
        assert "### Software Engineer II | **Uber**" in tailored.compiled_markdown
        assert "- Built low-latency gRPC services for driver location tracking." in tailored.compiled_markdown
        assert "## Education" in tailored.compiled_markdown
        assert "B.S. in Electrical and Computer Engineering" in tailored.compiled_markdown

        # Plain text must contain all sections
        assert "ALEX CHEN" in tailored.compiled_text
        assert "PROFESSIONAL SUMMARY" in tailored.compiled_text
        assert "TECHNICAL SKILLS" in tailored.compiled_text
        assert "WORK EXPERIENCE" in tailored.compiled_text
        assert "Senior Platform Engineer -- Datadog" in tailored.compiled_text
        assert "EDUCATION" in tailored.compiled_text

        # HTML must contain all sections and valid tags
        assert "<!DOCTYPE html>" in tailored.compiled_html
        assert "<h1>Alex Chen</h1>" in tailored.compiled_html
        assert "Datadog" in tailored.compiled_html
        assert "Uber" in tailored.compiled_html
        assert "UT Austin" in tailored.compiled_html

        # Traceability matrix must map cited verified facts
        assert tailored.traceability_matrix is not None
        assert len(tailored.traceability_matrix) > 0
        assert tailored.validation_details["verified_claims"] > 0

