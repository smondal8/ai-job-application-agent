from datetime import datetime, timezone
import html
from typing import Any, Dict, List, Optional


class ResumeDocumentCompiler:
    """Deterministic document compiler producing professional, ATS-optimized resumes and cover letters.
    
    Quality Standards:
    - High-fidelity typography, consistent 0.5in margins, and strong visual hierarchy.
    - Page-break controls and print CSS for multi-page support.
    - Graceful omission of missing/optional data (never emits 'None', 'null', or empty sections).
    - ATS-friendly semantic DOM structure.
    """

    def compile_html(
        self,
        candidate_info: Dict[str, Any],
        tailored_data: Dict[str, Any],
        educations: List[Dict[str, Any]],
        projects: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Deterministically render a high-fidelity, professional HTML resume matching Reactive Resume visual quality."""
        name = html.escape(candidate_info.get("full_name") or "Candidate")
        headline = html.escape(candidate_info.get("headline") or "")
        email = html.escape(candidate_info.get("email") or "")
        phone = html.escape(candidate_info.get("phone") or "")
        location = html.escape(candidate_info.get("location") or "")
        linkedin = candidate_info.get("linkedin_url") or ""
        github = candidate_info.get("github_url") or ""
        portfolio = candidate_info.get("portfolio_url") or candidate_info.get("website") or ""

        # Contact line items
        contact_items: List[str] = []
        if email:
            contact_items.append(f'<a href="mailto:{email}" class="contact-link">{email}</a>')
        if phone:
            contact_items.append(f'<span>{phone}</span>')
        if location:
            contact_items.append(f'<span>{location}</span>')
        if linkedin:
            clean_li = linkedin.replace("https://www.", "").replace("http://www.", "").replace("https://", "")
            contact_items.append(f'<a href="{html.escape(linkedin)}" target="_blank" class="contact-link">linkedin/{clean_li.split("/")[-1]}</a>')
        if github:
            clean_gh = github.replace("https://www.", "").replace("http://www.", "").replace("https://", "")
            contact_items.append(f'<a href="{html.escape(github)}" target="_blank" class="contact-link">github/{clean_gh.split("/")[-1]}</a>')
        if portfolio and portfolio != linkedin and portfolio != github:
            clean_p = portfolio.replace("https://www.", "").replace("http://www.", "").replace("https://", "").rstrip("/")
            contact_items.append(f'<a href="{html.escape(portfolio)}" target="_blank" class="contact-link">{clean_p}</a>')

        contact_html = ' <span class="bullet-sep">&bull;</span> '.join(contact_items)

        # 1. Summary Section
        summary_obj = tailored_data.get("tailored_summary") or candidate_info.get("summary")
        summary_text = summary_obj.get("text", "") if isinstance(summary_obj, dict) else str(summary_obj or "")
        summary_html = ""
        if summary_text and summary_text.strip() and summary_text.strip().lower() != "none":
            summary_html = f"""
            <section class="resume-section">
                <h2 class="section-title">Professional Summary</h2>
                <p class="summary-text">{html.escape(summary_text.strip())}</p>
            </section>
            """

        # 2. Skills Section
        skills_items = tailored_data.get("highlighted_skills") or candidate_info.get("skills") or []
        skills_html = ""
        if skills_items:
            categories: Dict[str, List[str]] = {}
            flat_skills: List[str] = []
            for sk in skills_items:
                if isinstance(sk, dict):
                    s_name = sk.get("name", "")
                    s_cat = sk.get("category") or "Core Competencies"
                    if s_name:
                        categories.setdefault(s_cat, []).append(s_name)
                        flat_skills.append(s_name)
                elif isinstance(sk, str) and sk.strip():
                    flat_skills.append(sk.strip())

            if len(categories) > 1:
                cat_rows = []
                for cat_name, s_names in categories.items():
                    clean_cat = cat_name.replace("_", " ").title()
                    badges = "".join(f'<span class="skill-tag">{html.escape(s)}</span>' for s in s_names if s)
                    cat_rows.append(f'<div class="skill-category-row"><span class="skill-category-label">{clean_cat}:</span> <div class="skill-badges-wrap">{badges}</div></div>')
                skills_content = "".join(cat_rows)
            else:
                badges = "".join(f'<span class="skill-tag">{html.escape(s)}</span>' for s in flat_skills if s)
                skills_content = f'<div class="skill-badges-wrap">{badges}</div>'

            skills_html = f"""
            <section class="resume-section">
                <h2 class="section-title">Technical Skills & Competencies</h2>
                <div class="skills-container">{skills_content}</div>
            </section>
            """

        # 3. Experience Section
        exp_list = tailored_data.get("tailored_experience") or candidate_info.get("experiences") or []
        exp_html = ""
        if exp_list:
            exp_blocks = []
            for exp in exp_list:
                comp = html.escape(exp.get("company") or "")
                pos = html.escape(exp.get("position") or "")
                exp_loc = html.escape(exp.get("location") or "")
                start = html.escape(str(exp.get("start_date") or ""))
                is_curr = exp.get("is_current")
                end = "Present" if is_curr else html.escape(str(exp.get("end_date") or ""))

                date_str = f"{start} – {end}" if (start and end) else (start or end or "")

                bullet_items = []
                highlights = exp.get("tailored_highlights") or exp.get("highlights") or exp.get("bullets") or []
                for h in highlights:
                    h_text = h.get("text", "") if isinstance(h, dict) else str(h)
                    if h_text and h_text.strip():
                        bullet_items.append(f'<li>{html.escape(h_text.strip())}</li>')

                desc_line = ""
                if not bullet_items and exp.get("description"):
                    d_text = str(exp["description"]).strip()
                    d_lines = [l.strip().lstrip("•-* ").strip() for l in d_text.split("\n") if l.strip()]
                    if len(d_lines) > 1:
                        bullet_items = [f'<li>{html.escape(l)}</li>' for l in d_lines]
                    else:
                        desc_line = f'<p class="exp-desc">{html.escape(d_text)}</p>'

                bullets_html = f'<ul class="exp-bullets">{"".join(bullet_items)}</ul>' if bullet_items else desc_line

                loc_span = f'<span class="entry-location">{exp_loc}</span>' if exp_loc else ''
                sub_row = f"""
                <div class="entry-sub">
                    <span class="entry-company">{comp}</span>
                    {loc_span}
                </div>
                """ if (comp or exp_loc) else ""

                exp_blocks.append(f"""
                <div class="entry-block">
                    <div class="entry-header">
                        <span class="entry-title"><strong>{pos}</strong></span>
                        <span class="entry-dates">{date_str}</span>
                    </div>
                    {sub_row}
                    {bullets_html}
                </div>
                """)

            exp_html = f"""
            <section class="resume-section">
                <h2 class="section-title">Professional Experience</h2>
                {"".join(exp_blocks)}
            </section>
            """

        # 4. Education Section
        edu_html = ""
        if educations:
            edu_blocks = []
            for edu in educations:
                inst = html.escape(edu.get("institution") or "")
                deg = html.escape(edu.get("degree") or "")
                field = html.escape(edu.get("field_of_study") or "")
                deg_full = f"{deg} in {field}" if (deg and field) else (deg or field or "Degree")
                start = html.escape(str(edu.get("start_date") or ""))
                end = html.escape(str(edu.get("end_date") or ""))
                date_str = f"{start} – {end}" if (start and end) else (start or end or "")
                gpa = html.escape(str(edu.get("gpa") or ""))
                gpa_span = f' <span class="edu-gpa">(GPA: {gpa})</span>' if gpa else ""

                edu_blocks.append(f"""
                <div class="entry-block">
                    <div class="entry-header">
                        <span class="entry-title"><strong>{deg_full}</strong>{gpa_span}</span>
                        <span class="entry-dates">{date_str}</span>
                    </div>
                    <div class="entry-sub">
                        <span class="entry-company">{inst}</span>
                    </div>
                </div>
                """)

            edu_html = f"""
            <section class="resume-section">
                <h2 class="section-title">Education</h2>
                {"".join(edu_blocks)}
            </section>
            """

        # 5. Projects Section
        proj_html = ""
        if projects:
            proj_blocks = []
            for p in projects:
                p_name = html.escape(p.get("name") or "Project")
                p_desc = html.escape(p.get("description") or "")
                p_url = p.get("url") or ""
                p_techs = p.get("technologies") or []
                if isinstance(p_techs, list):
                    tech_str = ", ".join(html.escape(t) for t in p_techs if t)
                else:
                    tech_str = html.escape(str(p_techs))

                title_el = f'<a href="{html.escape(p_url)}" target="_blank" class="project-link"><strong>{p_name}</strong></a>' if p_url else f'<strong>{p_name}</strong>'
                tech_span = f'<span class="entry-techs">[{tech_str}]</span>' if tech_str else ''

                bullets = "".join(f'<li>{html.escape(h)}</li>' for h in p.get("highlights", []) if h)
                bullets_ul = f'<ul class="exp-bullets">{bullets}</ul>' if bullets else ''
                desc_p = f'<p class="exp-desc">{p_desc}</p>' if p_desc else ''

                proj_blocks.append(f"""
                <div class="entry-block">
                    <div class="entry-header">
                        <span class="entry-title">{title_el} {tech_span}</span>
                    </div>
                    {desc_p}
                    {bullets_ul}
                </div>
                """)

            if proj_blocks:
                proj_html = f"""
                <section class="resume-section">
                    <h2 class="section-title">Selected Projects</h2>
                    {"".join(proj_blocks)}
                </section>
                """

        # Headline element
        headline_el = f'<div class="header-headline">{headline}</div>' if headline else ''

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — Resume</title>
<style>
  @page {{
    size: letter;
    margin: 0.5in;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.45;
    color: #1e293b;
    background-color: #ffffff;
    max-width: 820px;
    margin: 0 auto;
    padding: 24px 32px;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  
  /* Header */
  .resume-header {{
    text-align: center;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 12px;
    margin-bottom: 14px;
  }}
  .resume-header h1 {{
    font-size: 20pt;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #0f172a;
    line-height: 1.1;
    margin-bottom: 3px;
    text-transform: uppercase;
  }}
  .header-headline {{
    font-size: 10.5pt;
    font-weight: 600;
    color: #0284c7;
    margin-bottom: 6px;
    letter-spacing: 0.02em;
  }}
  .header-contact {{
    font-size: 9pt;
    color: #475569;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 6px;
  }}
  .contact-link {{
    color: #0f172a;
    text-decoration: none;
  }}
  .contact-link:hover {{
    color: #0284c7;
    text-decoration: underline;
  }}
  .bullet-sep {{
    color: #94a3b8;
    font-size: 8pt;
  }}

  /* Sections */
  .resume-section {{
    margin-bottom: 14px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .section-title {{
    font-size: 10pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #0f172a;
    border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 2px;
    margin-bottom: 8px;
    page-break-after: avoid;
    break-after: avoid;
  }}
  .summary-text {{
    font-size: 9.5pt;
    line-height: 1.5;
    color: #334155;
    text-align: justify;
    word-break: break-word;
  }}

  /* Entry Blocks */
  .entry-block {{
    margin-bottom: 10px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .entry-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 4px;
    font-size: 10pt;
  }}
  .entry-title {{
    color: #0f172a;
    font-size: 10pt;
    word-break: break-word;
    overflow-wrap: break-word;
  }}
  .entry-dates {{
    font-size: 9pt;
    font-weight: 500;
    color: #64748b;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}
  .entry-sub {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 4px;
    font-size: 9pt;
    margin-top: 1px;
    margin-bottom: 3px;
  }}
  .entry-company {{
    font-weight: 600;
    color: #334155;
    word-break: break-word;
  }}
  .entry-location {{
    color: #64748b;
    font-size: 8.5pt;
    font-style: italic;
  }}
  .entry-techs {{
    font-size: 8.5pt;
    color: #64748b;
    font-weight: normal;
    margin-left: 6px;
  }}
  .exp-desc {{
    font-size: 9.5pt;
    color: #334155;
    line-height: 1.45;
    margin-top: 2px;
    word-break: break-word;
  }}
  .exp-bullets {{
    margin: 3px 0 0 0;
    padding-left: 18px;
    list-style-type: disc;
  }}
  .exp-bullets li {{
    font-size: 9pt;
    line-height: 1.4;
    color: #334155;
    margin-bottom: 2.5px;
    word-break: break-word;
  }}

  /* Skills */
  .skills-container {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .skill-category-row {{
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 6px;
    font-size: 9pt;
    margin-bottom: 4px;
  }}
  .skill-category-label {{
    font-weight: 700;
    color: #1e293b;
    min-width: 120px;
    flex-shrink: 0;
  }}
  .skill-badges-wrap {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    flex: 1;
  }}
  .skill-tag, .skill-badge {{
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 8.5pt;
    font-weight: 500;
    line-height: 1.3;
    display: inline-block;
    word-break: break-word;
  }}

  /* Academics */
  .edu-gpa {{
    font-size: 8.5pt;
    font-weight: normal;
    color: #64748b;
  }}
  .project-link {{
    color: #0284c7;
    text-decoration: none;
  }}
  .project-link:hover {{
    text-decoration: underline;
  }}

  /* Media Print Adjustments */
  @media print {{
    body {{
      padding: 0;
      max-width: 100%;
      background: transparent;
    }}
    .no-print {{
      display: none;
    }}
  }}
</style>
</head>
<body>
  <header class="resume-header">
    <h1>{name}</h1>
    {headline_el}
    <div class="header-contact">{contact_html}</div>
  </header>

  {summary_html}
  {skills_html}
  {exp_html}
  {edu_html}
  {proj_html}
</body>
</html>"""

    def compile_markdown(
        self,
        candidate_info: Dict[str, Any],
        tailored_data: Dict[str, Any],
        educations: List[Dict[str, Any]],
        projects: Optional[List[Dict[str, Any]]] = None,
        include_traceability_annotations: bool = False,
    ) -> str:
        """Deterministically render an ATS-optimized clean Markdown resume."""
        name = candidate_info.get("full_name", "Candidate")
        headline = candidate_info.get("headline", "")
        email = candidate_info.get("email", "")
        phone = candidate_info.get("phone", "")
        location = candidate_info.get("location", "")
        linkedin = candidate_info.get("linkedin_url", "")
        github = candidate_info.get("github_url", "")
        portfolio = candidate_info.get("portfolio_url") or candidate_info.get("website", "")

        lines: List[str] = []

        # 1. Header
        lines.append(f"# {name}")
        if headline:
            lines.append(f"**{headline}**")

        contact_parts = [p for p in [email, phone, location] if p]
        if contact_parts:
            lines.append(" | ".join(contact_parts))

        links = [p for p in [linkedin, github, portfolio] if p]
        if links:
            lines.append(" | ".join(links))
        lines.append("\n---\n")

        # 2. Executive Summary
        summary_obj = tailored_data.get("tailored_summary") or candidate_info.get("summary")
        summary_text = summary_obj.get("text", "") if isinstance(summary_obj, dict) else str(summary_obj or "")
        summary_fids = summary_obj.get("source_fact_ids", []) if isinstance(summary_obj, dict) else []

        if summary_text and summary_text.strip() and summary_text.strip().lower() != "none":
            lines.append("## Professional Summary")
            if include_traceability_annotations and summary_fids:
                lines.append(f"{summary_text.strip()} `[^facts: {', '.join(summary_fids)}]`\n")
            else:
                lines.append(f"{summary_text.strip()}\n")

        # 3. Skills
        skills_items = tailored_data.get("highlighted_skills") or candidate_info.get("skills") or []
        if skills_items:
            lines.append("## Core Competencies & Technical Skills")
            skill_names = []
            for sk in skills_items:
                if isinstance(sk, dict):
                    skill_names.append(sk.get("name", ""))
                elif isinstance(sk, str):
                    skill_names.append(sk)
            clean_skills = [s.strip() for s in skill_names if s and s.strip()]
            if clean_skills:
                lines.append(", ".join(clean_skills) + "\n")

        # 4. Professional Experience
        exp_list = tailored_data.get("tailored_experience") or candidate_info.get("experiences") or []
        if exp_list:
            lines.append("## Professional Experience")
            for exp in exp_list:
                comp = exp.get("company", "Company")
                pos = exp.get("position", "Position")
                loc = exp.get("location", "")
                start = exp.get("start_date", "")
                end = "Present" if exp.get("is_current") else exp.get("end_date", "")
                date_str = f"{start} – {end}" if (start and end) else (start or end or "")
                loc_str = f" | {loc}" if loc else ""

                lines.append(f"### {pos} | **{comp}**{loc_str} `({date_str})`")

                highlights = exp.get("tailored_highlights") or exp.get("highlights") or exp.get("bullets") or []
                bullet_lines = []
                for h in highlights:
                    if isinstance(h, dict):
                        h_text = h.get("text", "")
                        h_fids = h.get("source_fact_ids", [])
                        if h_text and h_text.strip():
                            if include_traceability_annotations and h_fids:
                                bullet_lines.append(f"- {h_text.strip()} `[^{', '.join(h_fids)}]`")
                            else:
                                bullet_lines.append(f"- {h_text.strip()}")
                    elif isinstance(h, str) and h.strip():
                        bullet_lines.append(f"- {h.strip()}")

                if not bullet_lines and exp.get("description"):
                    d_text = str(exp["description"]).strip()
                    d_lines = [l.strip().lstrip("•-* ").strip() for l in d_text.split("\n") if l.strip()]
                    for l in d_lines:
                        bullet_lines.append(f"- {l}")

                for bl in bullet_lines:
                    lines.append(bl)
                lines.append("")

        # 5. Education
        if educations:
            lines.append("## Education")
            for edu in educations:
                inst = edu.get("institution", "Institution")
                deg = edu.get("degree", "Degree")
                field = edu.get("field_of_study", "")
                deg_full = f"{deg} in {field}" if (deg and field) else (deg or field or "Degree")
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
        projects: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Deterministically render plain ASCII text resume."""
        name = (candidate_info.get("full_name") or "CANDIDATE").upper()
        headline = candidate_info.get("headline", "")
        email = candidate_info.get("email", "")
        phone = candidate_info.get("phone", "")
        location = candidate_info.get("location", "")

        lines = [
            "=" * 70,
            f"  {name}",
        ]
        if headline:
            lines.append(f"  {headline}")

        contact_line = "  |  ".join(filter(None, [email, phone, location]))
        if contact_line:
            lines.append(f"  {contact_line}")
        lines.extend(["=" * 70, ""])

        # Summary
        summary_obj = tailored_data.get("tailored_summary") or candidate_info.get("summary")
        summary_text = summary_obj.get("text", "") if isinstance(summary_obj, dict) else str(summary_obj or "")
        if summary_text and summary_text.strip() and summary_text.strip().lower() != "none":
            lines.extend(["PROFESSIONAL SUMMARY", "-" * 40, summary_text.strip(), ""])

        # Skills
        skills = tailored_data.get("highlighted_skills") or candidate_info.get("skills") or []
        if skills:
            skill_names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in skills]
            clean_names = [s.strip() for s in skill_names if s and s.strip()]
            if clean_names:
                lines.extend(["TECHNICAL SKILLS", "-" * 40, ", ".join(clean_names), ""])

        # Experience
        experiences = tailored_data.get("tailored_experience") or candidate_info.get("experiences") or []
        if experiences:
            lines.extend(["WORK EXPERIENCE", "-" * 40])
            for exp in experiences:
                comp = exp.get("company", "Company")
                pos = exp.get("position", "Position")
                loc = exp.get("location", "")
                start = exp.get("start_date", "")
                end = "Present" if exp.get("is_current") else exp.get("end_date", "")
                date_str = f"{start} to {end}" if (start and end) else (start or end or "")
                loc_str = f" ({loc})" if loc else ""
                lines.append(f"{pos} -- {comp}{loc_str} ({date_str})")

                highlights = exp.get("tailored_highlights") or exp.get("highlights") or exp.get("bullets") or []
                bullet_lines = []
                for h in highlights:
                    h_text = h.get("text", "") if isinstance(h, dict) else str(h)
                    if h_text and h_text.strip():
                        bullet_lines.append(f"  * {h_text.strip()}")

                if not bullet_lines and exp.get("description"):
                    d_text = str(exp["description"]).strip()
                    d_lines = [l.strip().lstrip("•-* ").strip() for l in d_text.split("\n") if l.strip()]
                    for l in d_lines:
                        bullet_lines.append(f"  * {l}")

                for bl in bullet_lines:
                    lines.append(bl)
                lines.append("")

        # Education
        if educations:
            lines.extend(["EDUCATION", "-" * 40])
            for edu in educations:
                inst = edu.get("institution", "")
                deg = edu.get("degree", "")
                field = edu.get("field_of_study", "")
                full = f"{deg} in {field}" if (deg and field) else (deg or field or "Degree")
                start = edu.get("start_date", "")
                end = edu.get("end_date", "")
                date_str = f" ({start} to {end})" if (start or end) else ""
                lines.append(f"{full} -- {inst}{date_str}")
            lines.append("")

        # Projects
        if projects:
            lines.extend(["PROJECTS", "-" * 40])
            for p in projects:
                p_name = p.get("name", "Project")
                p_desc = p.get("description", "")
                lines.append(f"{p_name}: {p_desc}")
                for h in p.get("highlights", []):
                    if h:
                        lines.append(f"  * {h}")
            lines.append("")

        return "\n".join(lines)

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
            body_content = str(tailored_data.get("cover_letter") or f"I am writing to express my strong interest in the {role} opportunity at {company}.")

        header_lines = [name]
        contact_line = " | ".join(filter(None, [email, phone, location]))
        if contact_line:
            header_lines.append(contact_line)
        header_lines.extend([today_str, "", f"Hiring Team\n{company}", "", f"Dear {company} Hiring Team,", "", body_content, "", "Sincerely,", "", name])

        return "\n".join(header_lines)


resume_document_compiler = ResumeDocumentCompiler()
