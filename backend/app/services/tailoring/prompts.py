from typing import Any, Dict, List, Optional, Tuple

PROMPT_VERSION = "v1.0.0"
TAILORING_PROMPT_ID = "resume_tailoring_traceable_v1"


def build_traceable_tailoring_prompt(
    job_dict: Dict[str, Any],
    job_analysis_dict: Dict[str, Any],
    fact_registry_text: str,
    tone: str = "professional",
    target_role_title: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> Tuple[str, str]:
    """Construct a versioned prompt requiring strict atomic fact attribution for every tailored claim."""
    system_prompt = (
        f"You are a specialized Resume & Application Materials Tailoring Engine (Prompt Version: {PROMPT_VERSION}).\n"
        "You are strictly an EDITOR and STRATEGIC COMPOSER, NOT an author of fabricated candidate history.\n\n"
        "CORE RULES & CONSTRAINTS:\n"
        "1. STRICT FACT ATTRIBUTION: Every single tailored highlight, executive summary sentence, and cover letter paragraph "
        "MUST explicitly declare 'source_fact_ids' pointing to the verified fact IDs it derives from.\n"
        "2. NO HALLUCINATION: You may rephrase, emphasize metrics, and reorder bullet points to match the target job, but you MUST NEVER "
        "invent unverified employers, projects, metrics, degrees, or skills.\n"
        "3. COVER LETTER GROUNDING: The cover letter must only reference past accomplishments and skills traceable to verified facts.\n"
        "4. TONE & STYLE: Write in a compelling, concise, and impact-driven tone without buzzword fluff.\n"
        "5. STRUCTURED OUTPUT: Return strictly valid JSON conforming to the requested schema."
    )

    role_title = target_role_title or job_dict.get("title", "Target Role")
    company = job_dict.get("company", "Target Company")
    key_responsibilities = job_analysis_dict.get("key_responsibilities", [])
    matched_skills = job_analysis_dict.get("matched_skills", [])
    keywords = job_analysis_dict.get("keywords", [])
    fit_summary = job_analysis_dict.get("summary", "")

    user_prompt = f"""
### TARGET JOB POSITION
- Role Title: {role_title}
- Company: {company}
- Remote Policy: {job_dict.get('remote_type', 'unspecified')}
- Location: {job_dict.get('location', 'Unspecified')}
- Target Tone: {tone}

### JD ANALYSIS SIGNALS
- Role Summary: {job_analysis_dict.get('role_summary', '')}
- Key Responsibilities: {', '.join(key_responsibilities[:5])}
- High-Signal Keywords: {', '.join(keywords[:8])}
- Matched Skills: {', '.join(matched_skills[:8])}
- Assessment: {fit_summary}

{f'### CUSTOM USER INSTRUCTIONS\n{custom_instructions}\n' if custom_instructions else ''}

{fact_registry_text}

### OUTPUT SPECIFICATION
Generate tailored application materials grounded strictly in the candidate's verified facts provided above.
Return ONLY a valid JSON object matching this structure:
```json
{{
  "tailored_summary": {{
    "text": "Executive summary paragraph tailored for the target role...",
    "source_fact_ids": ["profile:1:headline", "exp:1:h0"]
  }},
  "tailored_experience": [
    {{
      "company": "Company Name",
      "position": "Position Title",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or null",
      "is_current": false,
      "tailored_highlights": [
        {{
          "text": "High-impact bullet point starting with strong action verb...",
          "source_fact_ids": ["exp:1:h0"]
        }}
      ]
    }}
  ],
  "highlighted_skills": [
    {{
      "name": "Skill Name",
      "source_fact_ids": ["skill:skill_id"]
    }}
  ],
  "cover_letter_paragraphs": [
    {{
      "paragraph_type": "opening",
      "text": "Opening paragraph expressing interest...",
      "source_fact_ids": ["profile:1:headline"]
    }},
    {{
      "paragraph_type": "body_experience",
      "text": "Body paragraph highlighting relevant accomplishments...",
      "source_fact_ids": ["exp:1:h0"]
    }},
    {{
      "paragraph_type": "closing",
      "text": "Closing paragraph...",
      "source_fact_ids": ["profile:1:headline"]
    }}
  ],
  "diff_summary": "Summary of tailoring strategy and key emphasized strengths."
}}
```
"""
    return system_prompt, user_prompt
