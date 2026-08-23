import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError, BadRequestError
from app.core.logging import get_logger
from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.audit import AuditLog
from app.services.llm.ollama_service import ollama_service, OllamaLLMService
from app.services.profile_service import profile_service
from app.services.jd_analysis_service import jd_analysis_service

logger = get_logger("app.services.resume_tailoring")
settings = get_settings()


class ResumeTailoringService:
    """Service for tailoring resumes and generating grounded cover letters using local Ollama LLM."""

    def __init__(self, llm_provider: Optional[OllamaLLMService] = None):
        self.llm = llm_provider or ollama_service

    async def tailor_application_materials(
        self,
        db: Session,
        job_id: int,
        candidate_profile_id: Optional[int] = None,
        tone: str = "professional",
        target_role_title: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> TailoredResume:
        """Tailor candidate resume and generate personalized cover letter grounded strictly in verified facts."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundError(f"Job listing with ID {job_id} not found.")

        # 1. Resolve candidate profile
        profile: Optional[CandidateProfile] = None
        if candidate_profile_id:
            profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_profile_id).first()
        else:
            profile = db.query(CandidateProfile).order_by(CandidateProfile.id.asc()).first()

        if not profile:
            raise BadRequestError("No candidate profile found. Please create a candidate profile before tailoring resumes.")

        # 2. Ensure JD Analysis exists
        analysis = (
            db.query(JobAnalysis)
            .filter(JobAnalysis.job_id == job.id, JobAnalysis.candidate_profile_id == profile.id)
            .first()
        )
        if not analysis:
            logger.info("No prior JD Analysis found for job %d. Running JD analysis first...", job.id)
            analysis = await jd_analysis_service.analyze_job(
                db=db,
                job_id=job.id,
                candidate_profile_id=profile.id,
            )

        # 3. Retrieve verified ground truth context
        ground_truth = profile_service.get_verified_ground_truth_context(db, profile.id)
        candidate_context_md = ground_truth["formatted_llm_prompt_context"]

        # 4. Construct anti-hallucination tailoring prompt
        system_prompt = (
            "You are a world-class technical career strategist and executive resume writer. "
            "Your task is to tailor a candidate's resume and write a personalized cover letter for a specific job opening. "
            "CRITICAL ANTI-HALLUCINATION RULES:\n"
            "1. NEVER invent, fabricate, or exaggerate companies, job titles, employment dates, degrees, projects, or metrics.\n"
            "2. You may ONLY draw upon facts, experiences, skills, and achievements explicitly provided in the AUTHORITATIVE CANDIDATE GROUND TRUTH.\n"
            "3. You may re-order, prioritize, and emphasize existing bullet points and highlight relevant skills to directly address the JD.\n"
            "4. The tailored summary must directly connect the candidate's verified achievements to the job's core technical challenges.\n"
            "5. The cover letter must be compelling, authentic, and free of generic clichés.\n"
            "6. Output valid JSON matching the requested schema exactly."
        )

        user_prompt = f"""
### TARGET JOB INFORMATION:
- **Role Title**: {target_role_title or job.title}
- **Company**: {job.company}
- **Location**: {job.location or 'Unspecified'}
- **Remote Policy**: {job.remote_type or 'Unspecified'}
- **Department**: {job.department or 'Unspecified'}
- **Role Summary**: {analysis.role_summary or job.title}
- **Key JD Keywords**: {', '.join(analysis.keywords or job.skills_raw or [])}
- **Matched Candidate Skills**: {', '.join(analysis.matched_skills or [])}

### JOB DESCRIPTION EXCERPT:
{job.description_clean or job.description_raw or job.title}

---

{candidate_context_md}

---
### TAILORING PREFERENCES:
- **Tone**: {tone}
{f'- **Custom Instructions**: {custom_instructions}' if custom_instructions else ''}

Please generate the tailored application materials and return a JSON object with this exact structure:
{{
  "tailored_summary": <string: 2-3 sentence impactful executive summary highlighting candidate's verified background for this specific role>,
  "highlighted_skills": [<string: verified skill 1>, <string: verified skill 2>, ... ordered by relevance to the JD],
  "tailored_experience": [
    {{
      "company": <string: exact company name from ground truth>,
      "position": <string: exact position from ground truth>,
      "start_date": <string>,
      "end_date": <string or null>,
      "is_current": <boolean>,
      "tailored_highlights": [<string: prioritized and polished bullet point 1 based strictly on verified experience>, ...]
    }}
  ],
  "cover_letter": <string: 3-4 paragraph persuasive, highly tailored cover letter addressing {job.company} and the {job.title} role>,
  "diff_summary": <string: 1-2 sentences summarizing key tailoring strategy used>
}}
"""

        logger.info(
            "Executing Resume Tailoring for job %d (%s) with candidate profile %d using model %s",
            job.id,
            job.title,
            profile.id,
            self.llm.model,
        )

        candidate_data = ground_truth.get("candidate", {})
        fallback_data = {
            "tailored_summary": f"Experienced {profile.headline or 'Engineer'} with proven track record across {', '.join(analysis.matched_skills[:3]) or 'software engineering'}.",
            "highlighted_skills": [s["name"] for s in ground_truth.get("skills", [])],
            "tailored_experience": [
                {
                    "company": exp.get("company"),
                    "position": exp.get("position"),
                    "start_date": exp.get("start_date"),
                    "end_date": exp.get("end_date"),
                    "is_current": exp.get("is_current", False),
                    "tailored_highlights": exp.get("highlights", []),
                }
                for exp in ground_truth.get("experiences", [])
            ],
            "cover_letter": (
                f"Dear Hiring Team at {job.company},\n\n"
                f"I am writing to express my strong enthusiasm for the {job.title} position. "
                f"With my background in {profile.headline or 'software engineering'}, I am excited by the opportunity to contribute to your team.\n\n"
                f"Sincerely,\n{candidate_data.get('full_name', profile.full_name)}"
            ),
            "diff_summary": "Tailored based on verified candidate profile.",
        }

        try:
            tailored_json = await self.llm.generate_structured_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                fallback_default=fallback_data,
            )
        except Exception as exc:
            logger.error("LLM resume tailoring failed: %s", exc)
            raise AppError(f"Resume tailoring failed: {exc}", status_code=502)

        # 5. Build full ATS Markdown resume content
        markdown_content = self._compile_markdown_resume(
            candidate=candidate_data,
            tailored_json=tailored_json,
            educations=ground_truth.get("educations", []),
            projects=ground_truth.get("projects", []),
            target_role=target_role_title or job.title,
            company=job.company,
        )

        # 6. Save or update TailoredResume in DB
        tailored_resume = (
            db.query(TailoredResume)
            .filter(TailoredResume.job_id == job.id, TailoredResume.candidate_profile_id == profile.id)
            .first()
        )
        if not tailored_resume:
            tailored_resume = TailoredResume(
                job_id=job.id,
                candidate_profile_id=profile.id,
            )
            db.add(tailored_resume)

        tailored_resume.candidate_profile_id = profile.id
        tailored_resume.tailored_summary = tailored_json.get("tailored_summary")
        tailored_resume.tailored_experience = tailored_json.get("tailored_experience", [])
        tailored_resume.highlighted_skills = tailored_json.get("highlighted_skills", [])
        tailored_resume.cover_letter = tailored_json.get("cover_letter")
        tailored_resume.markdown_content = markdown_content
        tailored_resume.diff_summary = tailored_json.get("diff_summary")
        tailored_resume.model_used = self.llm.model
        tailored_resume.status = "ready_for_review"
        tailored_resume.generation_metadata = {
            "model": self.llm.model,
            "provider": "ollama",
            "tone": tone,
            "fit_score": analysis.fit_score,
            "verified_facts_count": ground_truth["stats"]["total_verified_facts"],
        }

        # 7. Audit log
        audit = AuditLog(
            stage="resume_tailoring",
            action="RESUME_TAILORED",
            message=f"Generated tailored resume and cover letter for job {job.id} ({job.title} at {job.company}).",
            payload={
                "job_id": job.id,
                "candidate_profile_id": profile.id,
                "tailored_resume_id": tailored_resume.id,
                "model_used": self.llm.model,
                "tone": tone,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(tailored_resume)

        return tailored_resume

    def _compile_markdown_resume(
        self,
        candidate: Dict[str, Any],
        tailored_json: Dict[str, Any],
        educations: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        target_role: str,
        company: str,
    ) -> str:
        """Compile a clean, ATS-optimized Markdown resume."""
        name = candidate.get("full_name", "Candidate")
        email = candidate.get("email", "")
        phone = candidate.get("phone", "")
        location = candidate.get("location", "")
        linkedin = candidate.get("linkedin_url", "")
        github = candidate.get("github_url", "")

        contact_parts = [p for p in [email, phone, location, linkedin, github] if p]
        contact_line = " | ".join(contact_parts)

        lines = [
            f"# {name}",
            f"**Target Role: {target_role}**",
            contact_line,
            "",
            "## Professional Summary",
            tailored_json.get("tailored_summary", ""),
            "",
            "## Technical Skills",
            ", ".join(tailored_json.get("highlighted_skills", [])),
            "",
            "## Professional Experience",
        ]

        # Experience
        for exp in tailored_json.get("tailored_experience", []):
            end_date = "Present" if exp.get("is_current") else (exp.get("end_date") or "N/A")
            lines.append(f"\n### {exp.get('position')} — {exp.get('company')}")
            lines.append(f"*{exp.get('start_date')} – {end_date}*")
            for h in exp.get("tailored_highlights", []):
                lines.append(f"- {h}")

        # Education
        if educations:
            lines.append("\n## Education")
            for edu in educations:
                date_str = f" ({edu.get('start_date')} – {edu.get('end_date')})" if edu.get("start_date") else ""
                lines.append(f"- **{edu.get('degree')}** in {edu.get('field_of_study') or 'Studies'} — {edu.get('institution')}{date_str}")
                if edu.get("gpa"):
                    lines.append(f"  *GPA*: {edu.get('gpa')}")

        # Projects
        if projects:
            lines.append("\n## Key Projects")
            for proj in projects:
                lines.append(f"\n### {proj.get('name')}")
                if proj.get("url"):
                    lines.append(f"*Link*: {proj.get('url')}")
                if proj.get("description"):
                    lines.append(proj.get("description"))
                for h in proj.get("highlights", []):
                    lines.append(f"- {h}")

        return "\n".join(lines)

    def get_tailored_resume(self, db: Session, job_id: int) -> Optional[TailoredResume]:
        """Retrieve the latest tailored resume for a specific job."""
        return (
            db.query(TailoredResume)
            .filter(TailoredResume.job_id == job_id)
            .order_by(TailoredResume.updated_at.desc())
            .first()
        )

    def list_tailored_resumes(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
    ) -> List[TailoredResume]:
        """List tailored resumes paginated."""
        return (
            db.query(TailoredResume)
            .order_by(TailoredResume.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )


resume_tailoring_service = ResumeTailoringService()
