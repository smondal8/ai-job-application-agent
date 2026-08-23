from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ResumeDocumentCompiler:
    """Deterministic document compiler for ATS Markdown, Plain Text, HTML, and Cover Letters."""

    def compile_markdown(
        self,
        candidate_info: Dict[str, Any],
        tailored_data: Dict[str, Any],
        educations: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        include_traceability_annotations: bool = False,
    ) -> str:
        """Deterministically render an ATS-optimized Markdown resume."""
        name = candidate_info.get("full_name", "Candidate")
        email = candidate_info.get("email", "")
        phone = candidate_info.get("phone", "")
        location = candidate_info.get("location", "")
        linkedin = candidate_info.get("linkedin_url", "")
        github = candidate_info.get("github_url", "")
        portfolio = candidate_info.get("portfolio_url", "")

        lines: List[str] = []

        # 1. Header
        lines.append(f"# {name}")
        contact_parts = [p for p in [email, phone, location] if p]
        if contact_parts:
            lines.append(" | ".join(contact_parts))
        links = [p for p in [linkedin, github, portfolio] if p]
        if links:
            lines.append(" | ".join(links))
        lines.append("\n---\n")

        # 2. Executive Summary
        summary_obj = tailored_data.get("tailored_summary")
        summary_text = summary_obj.get("text", "") if isinstance(summary_obj, dict) else str(summary_obj or "")
        summary_fids = summary_obj.get("source_fact_ids", []) if isinstance(summary_obj, dict) else []

        if summary_text:
            lines.append("## Professional Summary")
            if include_traceability_annotations and summary_fids:
                lines.append(f"{summary_text} `[^facts: {', '.join(summary_fids)}]`\n")
            else:
                lines.append(f"{summary_text}\n")

        # 3. Core Competencies & Skills
        skills_items = tailored_data.get("highlighted_skills", [])
        if skills_items:
            lines.append("## Core Competencies & Technical Skills")
            skill_names = []
            for sk in skills_items:
                if isinstance(sk, dict):
                    skill_names.append(sk.get("name", ""))
                elif isinstance(sk, str):
                    skill_names.append(sk)
            clean_skills = [s for s in skill_names if s]
            lines.append(", ".join(clean_skills) + "\n")

        # 4. Professional Experience
        exp_list = tailored_data.get("tailored_experience", [])
        if exp_list:
            lines.append("## Professional Experience")
            for exp in exp_list:
                comp = exp.get("company", "Company")
                pos = exp.get("position", "Position")
                start = exp.get("start_date", "")
                end = "Present" if exp.get("is_current") else exp.get("end_date", "")
                date_str = f"{start} – {end}" if start else end

                lines.append(f"### {pos} | **{comp}** `({date_str})`")

                highlights = exp.get("tailored_highlights", [])
                for h in highlights:
                    if isinstance(h, dict):
                        h_text = h.get("text", "")
                        h_fids = h.get("source_fact_ids", [])
                        if include_traceability_annotations and h_fids:
                            lines.append(f"- {h_text} `[^{', '.join(h_fids)}]`")
                        else:
                            lines.append(f"- {h_text}")
                    elif isinstance(h, str) and h.strip():
                        lines.append(f"- {h.strip()}")
                lines.append("")

        # 5. Education
        if educations:
            lines.append("## Education")
            for edu in educations:
                inst = edu.get("institution", "Institution")
                deg = edu.get("degree", "Degree")
                field = edu.get("field_of_study", "")
                deg_full = f"{deg} in {field}" if field else deg
                start = edu.get("start_date", "")
                end = edu.get("end_date", "")
                date_str = f" ({start} - {end})" if (start or end) else ""
                lines.append(f"- **{deg_full}**, {inst}{date_str}")
            lines.append("")

        # 6. Selected Projects
        if projects:
            lines.append("## Key Projects")
            for p in projects:
                p_name = p.get("name", "Project")
                p_desc = p.get("description", "")
                lines.append(f"### {p_name}")
                if p_desc:
                    lines.append(f"{p_desc}")
                for h in p.get("highlights", []):
                    if h:
                        lines.append(f"- {h}")
                lines.append("")

        return "\n".join(lines)

    def compile_text(
        self,
        candidate_info: Dict[str, Any],
        tailored_data: Dict[str, Any],
        educations: List[Dict[str, Any]],
    ) -> str:
        """Deterministically render plain ASCII text resume."""
        name = (candidate_info.get("full_name") or "CANDIDATE").upper()
        email = candidate_info.get("email", "")
        phone = candidate_info.get("phone", "")
        location = candidate_info.get("location", "")

        lines = [
            "=" * 60,
            f"  {name}",
            f"  {email}  |  {phone}  |  {location}",
            "=" * 60,
            "",
        ]

        # Summary
        summary_obj = tailored_data.get("tailored_summary")
        summary_text = summary_obj.get("text", "") if isinstance(summary_obj, dict) else str(summary_obj or "")
        if summary_text:
            lines.extend(["PROFESSIONAL SUMMARY", "-" * 40, summary_text, ""])

        # Skills
        skills = tailored_data.get("highlighted_skills", [])
        if skills:
            skill_names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in skills]
            lines.extend(["TECHNICAL SKILLS", "-" * 40, ", ".join(filter(None, skill_names)), ""])

        # Experience
        experiences = tailored_data.get("tailored_experience", [])
        if experiences:
            lines.extend(["WORK EXPERIENCE", "-" * 40])
            for exp in experiences:
                comp = exp.get("company", "Company")
                pos = exp.get("position", "Position")
                start = exp.get("start_date", "")
                end = "Present" if exp.get("is_current") else exp.get("end_date", "")
                lines.append(f"{pos} -- {comp} ({start} to {end})")
                for h in exp.get("tailored_highlights", []):
                    h_text = h.get("text", "") if isinstance(h, dict) else str(h)
                    lines.append(f"  * {h_text}")
                lines.append("")

        # Education
        if educations:
            lines.extend(["EDUCATION", "-" * 40])
            for edu in educations:
                inst = edu.get("institution", "")
                deg = edu.get("degree", "")
                field = edu.get("field_of_study", "")
                full = f"{deg} in {field}" if field else deg
                lines.append(f"{full} -- {inst}")
            lines.append("")

        return "\n".join(lines)

    def compile_html(
        self,
        candidate_info: Dict[str, Any],
        tailored_data: Dict[str, Any],
        educations: List[Dict[str, Any]],
    ) -> str:
        """Deterministically render styled HTML resume."""
        name = candidate_info.get("full_name", "Candidate")
        email = candidate_info.get("email", "")
        phone = candidate_info.get("phone", "")
        location = candidate_info.get("location", "")

        summary_obj = tailored_data.get("tailored_summary")
        summary_text = summary_obj.get("text", "") if isinstance(summary_obj, dict) else str(summary_obj or "")

        skill_names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in tailored_data.get("highlighted_skills", [])]
        skills_html = "".join(f'<span class="skill-tag">{s}</span>' for s in skill_names if s)

        exp_html_parts = []
        for exp in tailored_data.get("tailored_experience", []):
            comp = exp.get("company", "")
            pos = exp.get("position", "")
            start = exp.get("start_date", "")
            end = "Present" if exp.get("is_current") else exp.get("end_date", "")
            bullets = "".join(
                f'<li>{h.get("text", "") if isinstance(h, dict) else str(h)}</li>'
                for h in exp.get("tailored_highlights", [])
            )
            exp_html_parts.append(f"""
            <div class="exp-block">
                <div class="exp-header">
                    <span class="exp-title"><strong>{pos}</strong> — {comp}</span>
                    <span class="exp-date">{start} – {end}</span>
                </div>
                <ul class="exp-bullets">{bullets}</ul>
            </div>
            """)

        edu_html_parts = []
        for edu in educations:
            inst = edu.get("institution", "")
            deg = edu.get("degree", "")
            field = edu.get("field_of_study", "")
            deg_full = f"{deg} in {field}" if field else deg
            edu_html_parts.append(f'<li><strong>{deg_full}</strong>, {inst}</li>')

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{name} — Resume</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #1e293b; max-width: 800px; margin: 0 auto; padding: 2rem; }}
  h1 {{ margin: 0 0 0.25rem; font-size: 1.75rem; color: #0f172a; }}
  .contact {{ color: #64748b; font-size: 0.875rem; margin-bottom: 1.5rem; }}
  h2 {{ font-size: 1.125rem; text-transform: uppercase; letter-spacing: 0.05em; color: #334155; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.25rem; margin-top: 1.5rem; }}
  .skill-tag {{ display: inline-block; background: #f1f5f9; color: #0f172a; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8125rem; margin: 0.2rem; font-weight: 500; }}
  .exp-block {{ margin-bottom: 1.25rem; }}
  .exp-header {{ display: flex; justify-content: space-between; font-size: 0.9375rem; margin-bottom: 0.25rem; }}
  .exp-date {{ color: #64748b; font-size: 0.8125rem; }}
  .exp-bullets {{ margin: 0.25rem 0 0; padding-left: 1.25rem; font-size: 0.875rem; }}
  .exp-bullets li {{ margin-bottom: 0.25rem; }}
</style>
</head>
<body>
  <h1>{name}</h1>
  <div class="contact">{email} &bull; {phone} &bull; {location}</div>
  
  <h2>Professional Summary</h2>
  <p>{summary_text}</p>
  
  <h2>Technical Skills</h2>
  <div>{skills_html}</div>
  
  <h2>Experience</h2>
  {"".join(exp_html_parts)}
  
  <h2>Education</h2>
  <ul>{"".join(edu_html_parts)}</ul>
</body>
</html>"""

    def compile_cover_letter(
        self,
        candidate_info: Dict[str, Any],
        job_info: Dict[str, Any],
        tailored_data: Dict[str, Any],
    ) -> str:
        """Deterministically format cover letter with candidate header, date, recipient, body, and closing."""
        name = candidate_info.get("full_name", "Candidate")
        email = candidate_info.get("email", "")
        phone = candidate_info.get("phone", "")
        location = candidate_info.get("location", "")

        company = job_info.get("company", "Hiring Team")
        role = job_info.get("title", "the open position")

        today_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

        paragraphs = tailored_data.get("cover_letter_paragraphs", [])
        body_text_list = []

        if paragraphs:
            for p in paragraphs:
                if isinstance(p, dict):
                    body_text_list.append(p.get("text", ""))
                elif isinstance(p, str):
                    body_text_list.append(p)
            body_content = "\n\n".join(filter(None, body_text_list))
        else:
            body_content = str(tailored_data.get("cover_letter") or "I am writing to express my strong interest in this opportunity.")

        return f"""{name}
{email} | {phone} | {location}
{today_str}

Hiring Team
{company}

Dear {company} Hiring Team,

{body_content}

Sincerely,

{name}"""


resume_document_compiler = ResumeDocumentCompiler()
