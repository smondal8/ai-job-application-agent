import pytest

from app.services.tailoring.compiler import resume_document_compiler


def test_compiler_markdown_and_plain_text():
    candidate_info = {
        "full_name": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "phone": "+1 (555) 019-2834",
        "location": "San Francisco, CA",
        "linkedin_url": "https://linkedin.com/in/jordanlee",
        "github_url": "https://github.com/jordanlee",
    }

    tailored_data = {
        "tailored_summary": {
            "text": "Staff Distributed Systems Engineer with 10+ years scaling low-latency consensus protocols.",
            "source_fact_ids": ["profile:1:headline", "exp:1"],
        },
        "highlighted_skills": [
            {"name": "Python", "source_fact_ids": ["skill:python"]},
            {"name": "Distributed Systems", "source_fact_ids": ["skill:dist"]},
            {"name": "FastAPI", "source_fact_ids": ["skill:fastapi"]},
        ],
        "tailored_experience": [
            {
                "company": "Stripe",
                "position": "Staff Infrastructure Engineer",
                "start_date": "2020-01",
                "end_date": None,
                "is_current": True,
                "tailored_highlights": [
                    {
                        "text": "Architected distributed consensus engine handling 500k transactions/sec.",
                        "source_fact_ids": ["exp:1:h0"],
                    }
                ],
            }
        ],
        "cover_letter_paragraphs": [
            {
                "paragraph_type": "opening",
                "text": "I am excited to apply for the Principal Infrastructure Engineer position.",
                "source_fact_ids": ["profile:1:headline"],
            },
            {
                "paragraph_type": "body",
                "text": "At Stripe, I spearheaded consensus engine optimizations handling massive throughput.",
                "source_fact_ids": ["exp:1:h0"],
            },
        ],
    }

    educations = [
        {
            "institution": "University of California, Berkeley",
            "degree": "B.S.",
            "field_of_study": "Computer Science",
            "start_date": "2012",
            "end_date": "2016",
        }
    ]
    projects = [
        {
            "name": "Raft-KV",
            "description": "Open-source distributed key-value store.",
            "highlights": ["Zero-downtime leader election"],
        }
    ]

    # 1. Compile Markdown
    md_output = resume_document_compiler.compile_markdown(
        candidate_info=candidate_info,
        tailored_data=tailored_data,
        educations=educations,
        projects=projects,
    )
    assert "# Jordan Lee" in md_output
    assert "jordan.lee@example.com" in md_output
    assert "## Professional Summary" in md_output
    assert "10+ years scaling low-latency" in md_output
    assert "## Core Competencies & Technical Skills" in md_output
    assert "Python, Distributed Systems, FastAPI" in md_output
    assert "### Staff Infrastructure Engineer | **Stripe**" in md_output
    assert "- Architected distributed consensus engine handling 500k transactions/sec." in md_output
    assert "## Education" in md_output
    assert "B.S. in Computer Science" in md_output
    assert "## Key Projects" in md_output

    # 2. Compile Text
    text_output = resume_document_compiler.compile_text(
        candidate_info=candidate_info,
        tailored_data=tailored_data,
        educations=educations,
    )
    assert "JORDAN LEE" in text_output
    assert "PROFESSIONAL SUMMARY" in text_output
    assert "WORK EXPERIENCE" in text_output
    assert "Staff Infrastructure Engineer -- Stripe" in text_output

    # 3. Compile HTML
    html_output = resume_document_compiler.compile_html(
        candidate_info=candidate_info,
        tailored_data=tailored_data,
        educations=educations,
    )
    assert "<!DOCTYPE html>" in html_output
    assert "<h1>Jordan Lee</h1>" in html_output
    assert '<span class="skill-tag">Python</span>' in html_output

    # 4. Compile Cover Letter
    job_info = {"title": "Principal Infrastructure Engineer", "company": "Netflix"}
    letter_output = resume_document_compiler.compile_cover_letter(
        candidate_info=candidate_info,
        job_info=job_info,
        tailored_data=tailored_data,
    )
    assert "Jordan Lee" in letter_output
    assert "Hiring Team" in letter_output
    assert "Netflix" in letter_output
    assert "Dear Netflix Hiring Team," in letter_output
    assert "I am excited to apply for the Principal Infrastructure Engineer position." in letter_output
    assert "Sincerely,\n\nJordan Lee" in letter_output
