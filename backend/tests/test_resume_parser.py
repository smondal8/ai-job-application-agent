from app.services.resume_parser_service import ResumeParserService


def test_parse_json_resume():
    parser = ResumeParserService()
    json_resume = """
    {
      "basics": {
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.org",
        "phone": "+1 555 999 0000",
        "headline": "Lead Defense Engineer",
        "summary": "Expert in cybernetic security systems."
      },
      "work": [
        {
          "company": "Cyberdyne Systems",
          "position": "Senior Engineer",
          "startDate": "2021-01",
          "endDate": "2023-12",
          "highlights": ["Designed defense core.", "Led 10 engineers."]
        }
      ],
      "education": [
        {
          "institution": "Caltech",
          "studyType": "B.S.",
          "area": "Computer Science"
        }
      ],
      "skills": [
        {"name": "Python", "level": "expert"},
        {"name": "C++", "level": "advanced"}
      ]
    }
    """
    result = parser.parse_raw_text(json_resume)
    assert result["provenance"] == "untrusted_import"
    assert result["is_verified"] is False
    assert result["profile"]["full_name"] == "Sarah Connor"
    assert result["profile"]["email"] == "sarah@cyberdyne.org"
    assert len(result["experiences"]) == 1
    assert result["experiences"][0]["company"] == "Cyberdyne Systems"
    assert result["experiences"][0]["is_verified"] is False
    assert len(result["skills"]) == 2
    assert result["skills"][0]["name"] == "Python"


def test_parse_plain_text_resume_never_invents_missing_facts():
    parser = ResumeParserService()
    text_resume = """
    Alexander Hamilton
    alexander@treasury.gov
    
    Summary
    Experienced financial architect and policy engineer.
    
    Skills
    Python, SQL, Financial Modeling, Distributed Ledgers
    
    Experience
    Senior Architect - First Bank of US
    - Designed treasury infrastructure.
    - Automated ledger reconciliation.
    
    Education
    King's College, B.A.
    """
    result = parser.parse_raw_text(text_resume)
    assert result["provenance"] == "untrusted_import"
    assert result["is_verified"] is False
    assert result["profile"]["email"] == "alexander@treasury.gov"
    # Verify phone was not invented (must be None)
    assert result["profile"]["phone"] is None
    assert len(result["skills"]) >= 3
    assert len(result["experiences"]) >= 1
    # All parsed facts must be untrusted/unverified
    for exp in result["experiences"]:
        assert exp["is_verified"] is False
