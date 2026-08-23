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
        "role_summary": "Architect the next generation frontend platform.",
        "seniority_level_inferred": "staff",
        "key_responsibilities": ["Lead UI architecture"],
        "required_qualifications": ["7+ years frontend"],
        "preferred_qualifications": ["Open source contributions"],
        "semantic_match_score": 92.0,
        "semantic_match_reasoning": "Excellent alignment with frontend architecture requirements.",
        "matched_skills": ["TypeScript"],
        "missing_skills": ["Next.js"],
        "keywords": ["TypeScript", "Frontend Architecture"],
        "red_flags": [],
        "recommendation": "strong_apply",
    }

    with patch("app.services.matching.semantic.SemanticMatcher.evaluate", new_callable=AsyncMock) as mock_sem:
        mock_sem.return_value = mock_analysis_json

        res = client.post(f"/api/v1/jobs/{job.id}/analyze", json={"candidate_profile_id": profile.id})
        assert res.status_code == 200
        analysis_data = res.json()
        assert analysis_data["job_id"] == job.id
        assert analysis_data["fit_score"] is not None
        assert analysis_data["fit_level"] is not None
        assert analysis_data["recommendation"] == "strong_apply"
        analysis_id = analysis_data["id"]

        # 4. Test GET /api/v1/jobs/{id}/analysis
        get_res = client.get(f"/api/v1/jobs/{job.id}/analysis")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == analysis_id

        # 5. Test GET /api/v1/analyses (list)
        list_res = client.get("/api/v1/analyses")
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1

        # 6. Test GET /api/v1/analyses/{id}
        detail_res = client.get(f"/api/v1/analyses/{analysis_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["id"] == analysis_id
