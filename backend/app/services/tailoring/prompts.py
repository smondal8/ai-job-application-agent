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
Generate tailored application materials grounded in the candidate's verified facts.
Return a valid JSON object matching this schema:
{{
  "tailored_summary": {{
    "text": <string: 2-3 sentence executive summary tailored for {role_title} at {company}>,
    "source_fact_ids": [<string: fact_id>, ...]
  }},
  "tailored_experience": [
    {{
      "company": <string: existing verified company name>,
      "position": <string: verified position title>,
      "start_date": <string>,
      "end_date": <string or null>,
      "is_current": <boolean>,
      "tailored_highlights": [
        {{
          "text": <string: high-impact bullet point starting with strong action verb and quantified outcome>,
          "source_fact_ids": [<string: exact fact_id, e.g. "exp:1:h0", "skill:python">]
        }}
      ]
    }}
  ],
  "highlighted_skills": [
    {{
      "name": <string: skill name>,
      "source_fact_ids": [<string: exact skill fact_id, e.g. "skill:fastapi">]
    }}
  ],
  "cover_letter_paragraphs": [
    {{
      "paragraph_type": <"opening" | "body_experience" | "body_skills" | "closing">,
      "text": <string: tailored paragraph for {company}>,
      "source_fact_ids": [<string: fact_id>, ...]
    }}
  ],
  "diff_summary": <string: concise 1-2 sentence explanation of tailoring strategy and key emphasized strengths>
}}
"""
    return system_prompt, user_prompt
