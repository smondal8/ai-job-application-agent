import pytest

from app.services.tailoring.fact_registry import AtomicFactRegistry
from app.services.tailoring.validator import traceability_validator


@pytest.fixture
def mock_fact_registry() -> AtomicFactRegistry:
    registry = AtomicFactRegistry()
    registry.register("profile:1:headline", "profile", "Staff Infrastructure Engineer")
    registry.register("exp:1", "experience", "Staff Engineer at Stripe")
    registry.register("exp:1:h0", "experience", "Scaled ledger processing to 500k ops/sec with Raft consensus.")
    registry.register("exp:1:h1", "experience", "Reduced p99 API latency by 45% using distributed caching.")
    registry.register("skill:python", "skill", "Python (languages, expert)")
    registry.register("skill:fastapi", "skill", "FastAPI (frameworks, expert)")
    registry.register("edu:1", "education", "B.S. in Computer Science, University of Washington")
    return registry


def test_validator_all_valid_claims(mock_fact_registry: AtomicFactRegistry):
    valid_tailored_data = {
        "tailored_summary": {
            "text": "Staff Infrastructure Engineer specializing in high-throughput distributed systems.",
            "source_fact_ids": ["profile:1:headline", "exp:1"],
        },
        "tailored_experience": [
            {
                "company": "Stripe",
                "position": "Staff Engineer",
                "tailored_highlights": [
                    {
                        "text": "Engineered distributed streaming ledger capable of 500,000 ops/sec using Raft consensus.",
                        "source_fact_ids": ["exp:1:h0"],
                    },
                    {
                        "text": "Optimized p99 latency by 45% through robust multi-tier caching architectures.",
                        "source_fact_ids": ["exp:1:h1"],
                    },
                ],
            }
        ],
        "highlighted_skills": [
            {"name": "Python", "source_fact_ids": ["skill:python"]},
            {"name": "FastAPI", "source_fact_ids": ["skill:fastapi"]},
        ],
        "cover_letter_paragraphs": [
            {
                "paragraph_type": "opening",
                "text": "I am thrilled to apply for the Principal Engineer position.",
                "source_fact_ids": ["profile:1:headline"],
            },
            {
                "paragraph_type": "body_experience",
                "text": "At Stripe, I scaled high-throughput ledger engines handling 500k ops/sec.",
                "source_fact_ids": ["exp:1:h0"],
            },
        ],
    }

    result = traceability_validator.validate(valid_tailored_data, mock_fact_registry)

    assert result.is_valid is True
    assert result.status == "valid"
    assert result.traceability_score == 100.0
    assert len(result.untraced_claims) == 0
    assert "exp:1:h0" in result.traceability_matrix
    assert len(result.traceability_matrix["exp:1:h0"]) >= 2  # Used in exp and cover letter


def test_validator_catches_untraced_and_hallucinated_claims(mock_fact_registry: AtomicFactRegistry):
    hallucinated_tailored_data = {
        "tailored_summary": {
            "text": "Ph.D. in Quantum Computing from MIT with 15 years at Google.",
            "source_fact_ids": ["unverified:mit:phd", "unverified:google:15yrs"],  # Unknown IDs
        },
        "tailored_experience": [
            {
                "company": "Stripe",
                "position": "Staff Engineer",
                "tailored_highlights": [
                    {
                        "text": "Scaled ledger processing to 500k ops/sec.",
                        "source_fact_ids": ["exp:1:h0"],  # Valid
                    },
                    {
                        "text": "Invented brand new quantum compiler saving $50M.",
                        "source_fact_ids": [],  # Empty ID
                    },
                ],
            }
        ],
        "highlighted_skills": [
            {"name": "Quantum Computing", "source_fact_ids": ["skill:quantum"]},  # Unknown ID
        ],
    }

    result = traceability_validator.validate(hallucinated_tailored_data, mock_fact_registry)

    assert result.is_valid is False
    assert result.status in ["requires_human_review", "rejected"]
    assert result.traceability_score < 75.0
    assert len(result.untraced_claims) >= 3

    untraced_reasons = [u.reason for u in result.untraced_claims]
    assert any("Missing source_fact_ids" in r for r in untraced_reasons)
    assert any("None of the referenced source_fact_ids match" in r for r in untraced_reasons)
