from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, WorkExperience, CandidateSkill
from app.models.analysis import JobAnalysis


def test_phase6_tailoring_api_endpoints(client: TestClient, db_session: Session):
    # 1. Setup candidate profile and job
    profile = CandidateProfile(
        full_name="Alex River",
        email="alex.river@example.com",
        headline="Principal Platform Engineer",
        summary="Specializing in scalable distributed systems and realtime APIs.",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    exp = WorkExperience(
        profile_id=profile.id,
        company="Figma",
        position="Senior Software Engineer",
        start_date="2021",
        is_verified=True,
        highlights=["Built canvas streaming synchronization protocol."],
        skills_used=["TypeScript", "React", "Rust"],
    )
    skill1 = CandidateSkill(profile_id=profile.id, name="TypeScript", category="languages", proficiency="expert", is_verified=True)
    skill2 = CandidateSkill(profile_id=profile.id, name="React", category="frameworks", proficiency="expert", is_verified=True)
    db_session.add_all([exp, skill1, skill2])
    db_session.commit()
    db_session.refresh(exp)

    job = Job(
        title="Staff Frontend Architect",
        company="Vercel",
        location="Remote",
        remote_type="remote",
        description_raw="Seeking Frontend Architect with deep TypeScript and real-time state synchronization skills.",
        skills_raw=["TypeScript", "React", "Next.js"],
        source="unit_test",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=profile.id,
        fit_score=92.0,
        fit_level="high",
        recommendation="strong_apply",
        matched_skills=["TypeScript", "React"],
        missing_skills=["Next.js"],
        status="completed",
    )
    db_session.add(analysis)
    db_session.commit()

    # 2. Mock LLM Response
    mock_tailor_json = {
        "tailored_summary": {
            "text": "Principal Platform Engineer with expertise in real-time UI synchronization and scalable systems.",
            "source_fact_ids": [f"profile:{profile.id}:headline", f"exp:{exp.id}"],
        },
        "highlighted_skills": [
            {"name": "TypeScript", "source_fact_ids": [f"skill:{skill1.id}"]},
            {"name": "React", "source_fact_ids": [f"skill:{skill2.id}"]},
        ],
        "tailored_experience": [
            {
                "company": "Figma",
                "position": "Senior Software Engineer",
                "start_date": "2021",
                "end_date": None,
                "is_current": True,
                "tailored_highlights": [
                    {
                        "text": "Engineered canvas streaming synchronization protocol handling millions of real-time events.",
                        "source_fact_ids": [f"exp:{exp.id}:h0"],
                    }
                ],
            }
        ],
        "cover_letter_paragraphs": [
            {
                "paragraph_type": "opening",
                "text": "I am writing to express my enthusiasm for the Staff Frontend Architect position at Vercel.",
                "source_fact_ids": [f"profile:{profile.id}:headline"],
            },
            {
                "paragraph_type": "body_experience",
                "text": "At Figma, I developed canvas streaming synchronization handling high-throughput real-time updates.",
                "source_fact_ids": [f"exp:{exp.id}:h0"],
            },
        ],
        "diff_summary": "Emphasized real-time streaming synchronization achievements for Vercel platform role.",
    }

    with patch("app.services.llm.ollama_service.OllamaLLMService.generate_structured_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_tailor_json

        # 3. Test POST /api/v1/jobs/{id}/tailor-resume
        res = client.post(
            f"/api/v1/jobs/{job.id}/tailor-resume",
            json={"candidate_profile_id": profile.id, "tone": "technical"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["job_id"] == job.id
        assert data["prompt_version"] == "v1.0.0"
        assert data["validation_status"] == "valid"
        assert data["validation_details"]["traceability_score"] == 100.0
        assert "Principal Platform Engineer" in data["tailored_summary"]
        assert data["compiled_markdown"] is not None
        assert data["compiled_text"] is not None
        assert data["compiled_html"] is not None
        tailor_id = data["id"]

        # 4. Test GET /api/v1/jobs/{id}/tailored-resume
        get_res = client.get(f"/api/v1/jobs/{job.id}/tailored-resume")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == tailor_id

        # 5. Test GET /api/v1/tailored-resumes
        list_res = client.get("/api/v1/tailored-resumes")
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1

        # 6. Test GET /api/v1/tailored-resumes/{id}
        detail_res = client.get(f"/api/v1/tailored-resumes/{tailor_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["id"] == tailor_id
        assert detail_res.json()["traceability_matrix"] is not None

        # 7. Test POST /api/v1/tailored-resumes/{id}/approve
        approve_res = client.post(
            f"/api/v1/tailored-resumes/{tailor_id}/approve",
            json={"approver_notes": "Reviewed and approved for submission."},
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "approved"
        assert approve_res.json()["human_approved_at"] is not None

        # 8. Test GET /api/v1/tailored-resumes/{id}/download?format=markdown
        dl_md = client.get(f"/api/v1/tailored-resumes/{tailor_id}/download?format=markdown")
        assert dl_md.status_code == 200
        assert "# Alex River" in dl_md.text

        # 9. Test GET /api/v1/tailored-resumes/{id}/download?format=text
        dl_text = client.get(f"/api/v1/tailored-resumes/{tailor_id}/download?format=text")
        assert dl_text.status_code == 200
        assert "ALEX RIVER" in dl_text.text

        # 10. Test GET /api/v1/tailored-resumes/{id}/download?format=html
        dl_html = client.get(f"/api/v1/tailored-resumes/{tailor_id}/download?format=html")
        assert dl_html.status_code == 200
        assert "<h1>Alex River</h1>" in dl_html.text

        # 11. Test GET /api/v1/tailored-resumes/{id}/download?format=cover_letter
        dl_cl = client.get(f"/api/v1/tailored-resumes/{tailor_id}/download?format=cover_letter")
        assert dl_cl.status_code == 200
        assert "Dear Vercel Hiring Team," in dl_cl.text
