import pytest

from app.services.matching.deterministic import deterministic_matcher


def test_deterministic_normalize_term():
    assert deterministic_matcher.normalize_term("  React.js  ") == "react.js"
    assert deterministic_matcher.normalize_term("C++ (Advanced)") == "c++ advanced"
    assert deterministic_matcher.normalize_term("FastAPI!") == "fastapi"


def test_deterministic_skill_matching_exact_and_alias():
    candidate_skills = [
        {"name": "Python", "category": "languages"},
        {"name": "FastAPI", "category": "frameworks"},
        {"name": "PostgreSQL", "category": "databases"},
        {"name": "Kubernetes", "category": "cloud_devops"},
    ]

    job_skills_raw = ["python3", "fast-api", "k8s", "rust"]
    job_description = "We are seeking a senior backend engineer with deep Python, FastAPI, and K8s expertise. Experience with Rust is a plus."

    matched, missing, score = deterministic_matcher.match_skills(
        candidate_skills=candidate_skills,
        job_skills_raw=job_skills_raw,
        job_description_text=job_description,
    )

    # 3 matched (Python, FastAPI, Kubernetes), 1 missing (Rust)
    assert "Python" in matched
    assert "FastAPI" in matched
    assert "Kubernetes" in matched
    assert "rust" in missing or "Rust" in missing
    assert score == 75.0  # 3 / 4 * 100


def test_deterministic_criteria_evaluation():
    candidate_facts = {
        "candidate": {"location": "San Francisco, CA"},
        "experiences": [
            {"company": "Stripe", "position": "Senior Engineer"},
            {"company": "Google", "position": "Software Engineer"},
            {"company": "Meta", "position": "Software Engineer"},
        ],
    }

    # 1. Job requiring 5 years, candidate has ~6 years
    job_data_match = {
        "location": "San Francisco, CA",
        "remote_type": "hybrid",
        "experience_years_min": 5,
    }
    eval_res = deterministic_matcher.evaluate_criteria(candidate_facts, job_data_match)
    assert eval_res["experience_meets_min"] is True
    assert eval_res["remote_compatible"] is True

    # 2. Onsite job in New York for candidate in SF
    job_data_mismatch = {
        "location": "New York, NY",
        "remote_type": "on_site",
        "experience_years_min": 10,
    }
    eval_mismatch = deterministic_matcher.evaluate_criteria(candidate_facts, job_data_mismatch)
    assert eval_mismatch["experience_meets_min"] is False
    assert eval_mismatch["remote_compatible"] is False
