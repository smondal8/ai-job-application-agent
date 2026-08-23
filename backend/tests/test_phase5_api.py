from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, WorkExperience, CandidateSkill


def test_phase5_api_endpoints(client: TestClient, db_session: Session):
    # 1. Test LLM Status endpoint
    llm_status_mock = {
        "provider": "ollama",
        "status": "connected",
        "base_url": "http://127.0.0.1:11434",
        "active_model": "qwen3:8b",
        "is_active_model_available": True,
        "available_models": ["qwen3:8b"],
        "latency_ms": 1.25,
        "error": None,
    }

    with patch("app.services.llm.ollama_service.OllamaLLMService.check_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = llm_status_mock

        res = client.get("/api/v1/llm/status")
        assert res.status_code == 200
        data = res.json()
        assert data["provider"] == "ollama"
        assert data["active_model"] == "qwen3:8b"
        assert data["is_active_model_available"] is True

    # 2. Setup candidate profile and job
    profile = CandidateProfile(
        full_name="Alex River",
        email="alex.river@example.com",
        headline="Principal Platform Engineer",
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
        highlights=["Built canvas streaming synchronization."],
    )
    skill = CandidateSkill(profile_id=profile.id, name="TypeScript", category="languages", proficiency="expert", is_verified=True)
    db_session.add_all([exp, skill])
    db_session.commit()

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

    # 3. Test POST /api/v1/jobs/{id}/analyze
    mock_analysis_json = {
        "fit_score": 90.0,
        "fit_level": "high",
        "summary": "Excellent alignment with frontend architecture requirements.",
        "role_summary": "Architect the next generation frontend platform.",
        "key_responsibilities": ["Lead UI architecture"],
        "matched_skills": ["TypeScript"],
        "missing_skills": ["Next.js"],
        "required_qualifications": ["7+ years frontend"],
        "preferred_qualifications": ["Open source contributions"],
        "keywords": ["TypeScript", "Frontend Architecture"],
    }

    with patch("app.services.llm.ollama_service.OllamaLLMService.generate_structured_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_analysis_json

        res = client.post(f"/api/v1/jobs/{job.id}/analyze", json={"candidate_profile_id": profile.id})
        assert res.status_code == 200
        analysis_data = res.json()
        assert analysis_data["job_id"] == job.id
        assert analysis_data["fit_score"] == 90.0
        assert analysis_data["fit_level"] == "high"

        # 4. Test GET /api/v1/jobs/{id}/analysis
        get_res = client.get(f"/api/v1/jobs/{job.id}/analysis")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == analysis_data["id"]

    # 5. Test POST /api/v1/jobs/{id}/tailor
    mock_tailor_json = {
        "tailored_summary": "Principal Platform Engineer with expertise in real-time UI synchronization and scalable systems.",
        "highlighted_skills": ["TypeScript", "React", "State Sync"],
        "tailored_experience": [
            {
                "company": "Figma",
                "position": "Senior Software Engineer",
                "start_date": "2021",
                "end_date": None,
                "is_current": True,
                "tailored_highlights": ["Engineered canvas synchronization handling millions of events."],
            }
        ],
        "cover_letter": "Dear Vercel Team,\n\nI am eager to contribute to your frontend infrastructure...",
        "diff_summary": "Tailored towards real-time web infrastructure.",
    }

    with patch("app.services.llm.ollama_service.OllamaLLMService.generate_structured_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_tailor_json

        res = client.post(
            f"/api/v1/jobs/{job.id}/tailor",
            json={"candidate_profile_id": profile.id, "tone": "professional"},
        )
        assert res.status_code == 200
        tailor_data = res.json()
        assert tailor_data["job_id"] == job.id
        assert "Principal Platform Engineer" in tailor_data["tailored_summary"]
        assert tailor_data["markdown_content"] is not None
        tailor_id = tailor_data["id"]

        # 6. Test GET /api/v1/jobs/{id}/tailored-resume
        get_tailor_res = client.get(f"/api/v1/jobs/{job.id}/tailored-resume")
        assert get_tailor_res.status_code == 200
        assert get_tailor_res.json()["id"] == tailor_id

        # 7. Test GET /api/v1/tailored-resumes
        list_res = client.get("/api/v1/tailored-resumes")
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1

        # 8. Test GET /api/v1/tailored-resumes/{id}
        detail_res = client.get(f"/api/v1/tailored-resumes/{tailor_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["id"] == tailor_id
