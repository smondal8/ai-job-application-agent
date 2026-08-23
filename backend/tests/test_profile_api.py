from fastapi.testclient import TestClient


def test_get_and_update_primary_profile_api(client: TestClient):
    # 1. Get Primary Profile
    get_res = client.get("/api/v1/profile")
    assert get_res.status_code == 200
    profile_data = get_res.json()
    profile_id = profile_data["id"]

    # 2. Update Profile
    update_res = client.put(
        f"/api/v1/profile/{profile_id}",
        json={
            "full_name": "Claude Shannon",
            "email": "claude@bell-labs.com",
            "headline": "Father of Information Theory",
            "location": "Murray Hill, NJ",
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Claude Shannon"


def test_experience_and_skills_api_crud(client: TestClient):
    profile_res = client.get("/api/v1/profile")
    profile_id = profile_res.json()["id"]

    # 1. Add Experience
    exp_payload = {
        "company": "Bell Laboratories",
        "position": "Research Mathematician",
        "start_date": "1941",
        "end_date": "1972",
        "highlights": ["Published Mathematical Theory of Communication."],
        "skills_used": ["Information Theory", "Cryptography"],
    }
    create_exp_res = client.post(f"/api/v1/profile/{profile_id}/experiences", json=exp_payload)
    assert create_exp_res.status_code == 201
    exp_id = create_exp_res.json()["id"]
    assert create_exp_res.json()["is_verified"] is False

    # 2. Toggle Experience Verification
    verify_exp_res = client.post(f"/api/v1/profile/experiences/{exp_id}/verify?verified=true")
    assert verify_exp_res.status_code == 200
    assert verify_exp_res.json()["is_verified"] is True

    # 3. Add Skills Bulk
    skills_payload = {
        "skills": [
            {"name": "Information Theory", "category": "foundations", "proficiency": "expert"},
            {"name": "Signal Processing", "category": "engineering", "proficiency": "advanced"},
        ]
    }
    bulk_res = client.post(f"/api/v1/profile/{profile_id}/skills/bulk", json=skills_payload)
    assert bulk_res.status_code == 201
    assert len(bulk_res.json()) == 2


def test_raw_resume_ingestion_api(client: TestClient):
    profile_res = client.get("/api/v1/profile")
    profile_id = profile_res.json()["id"]

    # 1. Ingest via raw text endpoint
    text_payload = {
        "raw_text": """
        John von Neumann
        vonneumann@ias.edu
        
        Experience
        Professor - Institute for Advanced Study
        - Developed game theory and cellular automata.
        
        Skills
        Applied Mathematics, Quantum Mechanics, Architecture
        """,
        "label": "Von Neumann Resume",
    }
    import_res = client.post("/api/v1/resumes/imports/text", json=text_payload)
    assert import_res.status_code == 201
    import_data = import_res.json()
    import_id = import_data["id"]
    assert import_data["status"] == "parsed"
    assert import_data["file_hash"] is not None

    # 2. Ingest via multipart file upload
    file_content = b"Grace Hopper\ngrace@navy.mil\nSkills: COBOL, Compilers"
    upload_res = client.post(
        "/api/v1/resumes/imports/upload",
        files={"file": ("hopper_resume.txt", file_content, "text/plain")},
        data={"profile_id": str(profile_id)},
    )
    assert upload_res.status_code == 201
    assert upload_res.json()["filename"] == "hopper_resume.txt"

    # 3. Apply import to profile
    apply_res = client.post(f"/api/v1/resumes/imports/{import_id}/apply-to-profile?profile_id={profile_id}")
    assert apply_res.status_code == 200
    applied_profile = apply_res.json()
    assert applied_profile["full_name"] == "John von Neumann"
    # Transferred facts must be unverified
    assert applied_profile["is_verified"] is False


def test_authoritative_llm_ground_truth_context_api(client: TestClient):
    profile_res = client.get("/api/v1/profile")
    profile_id = profile_res.json()["id"]

    # Add 1 verified skill and 1 unverified skill
    client.post(
        f"/api/v1/profile/{profile_id}/skills",
        json={"name": "Verified Math Skill", "category": "math", "proficiency": "expert"},
    )
    unverified_skill_res = client.post(
        f"/api/v1/profile/{profile_id}/skills",
        json={"name": "Unverified Ghost Skill", "category": "secret", "proficiency": "beginner"},
    )
    skill_to_verify_id = client.get("/api/v1/profile").json()["skills"][0]["id"]
    client.post(f"/api/v1/profile/skills/{skill_to_verify_id}/verify?verified=true")

    # Get authoritative ground truth context
    gt_res = client.get(f"/api/v1/profile/{profile_id}/verified-context")
    assert gt_res.status_code == 200
    gt_data = gt_res.json()

    assert "formatted_llm_prompt_context" in gt_data
    # Verified skills must be present
    assert any(s["name"] == "Verified Math Skill" for s in gt_data["skills"])
    # Unverified skills MUST be absent
    assert not any(s["name"] == "Unverified Ghost Skill" for s in gt_data["skills"])
