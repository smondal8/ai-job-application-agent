from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError, BadRequestError
from app.core.logging import get_logger
from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.analysis import JobAnalysis
from app.models.audit import AuditLog
from app.services.llm.ollama_service import ollama_service, OllamaLLMService
from app.services.profile_service import profile_service

logger = get_logger("app.services.jd_analysis")
settings = get_settings()


class JDAnalysisService:
    """Service for deep Job Description analysis and candidate alignment using local Ollama LLM."""

    def __init__(self, llm_provider: Optional[OllamaLLMService] = None):
        self.llm = llm_provider or ollama_service

    async def analyze_job(
        self,
        db: Session,
        job_id: int,
        candidate_profile_id: Optional[int] = None,
        custom_instructions: Optional[str] = None,
    ) -> JobAnalysis:
        """Perform structured AI analysis of a job listing against verified candidate facts."""
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
            raise BadRequestError("No candidate profile found. Please create a candidate profile before analyzing jobs.")

        # 2. Retrieve verified ground truth context (Strict anti-hallucination boundary)
        ground_truth = profile_service.get_verified_ground_truth_context(db, profile.id)
        candidate_context_md = ground_truth["formatted_llm_prompt_context"]

        # 3. Construct system prompt & user prompt
        system_prompt = (
            "You are an expert technical recruiter and talent evaluator for software and engineering roles. "
            "Your task is to perform an objective, deep analysis of a job description and evaluate how well "
            "the candidate matches the role based STRICTLY on their verified profile. "
            "RULES:\n"
            "1. NEVER fabricate, assume, or invent skills, degrees, or experiences that are not in the Candidate Ground Truth.\n"
            "2. Matched skills must ONLY contain skills the candidate actually has verified.\n"
            "3. Missing skills should list important skills or requirements mentioned in the JD that the candidate lacks.\n"
            "4. Calculate an objective fit_score between 0 and 100 based on technical match, seniority, and responsibilities.\n"
            "5. Output valid JSON matching the requested schema exactly."
        )

        user_prompt = f"""
### JOB LISTING DETAILS:
- **Title**: {job.title}
- **Company**: {job.company}
- **Location**: {job.location or 'Unspecified'}
- **Remote Policy**: {job.remote_type or 'Unspecified'}
- **Department**: {job.department or 'Unspecified'}
- **Seniority**: {job.seniority_level or 'Unspecified'}
- **Raw Skills / Tags**: {', '.join(job.skills_raw or [])}

### JOB DESCRIPTION:
{job.description_clean or job.description_raw or 'No full description provided. Evaluate based on title and metadata.'}

---

{candidate_context_md}

---
{f'### ADDITIONAL EVALUATION INSTRUCTIONS:\n{custom_instructions}' if custom_instructions else ''}

Please evaluate the candidate against this job description and return a JSON object with this exact structure:
{{
  "fit_score": <number between 0 and 100, e.g. 85>,
  "fit_level": <"high" | "medium" | "low">,
  "summary": <string: 2-3 sentences evaluating why this is or is not a strong match>,
  "role_summary": <string: 1-2 sentences summarizing the core focus of the role>,
  "key_responsibilities": [<string: responsibility 1>, <string: responsibility 2>, ...],
  "matched_skills": [<string: verified skill 1>, <string: verified skill 2>, ...],
  "missing_skills": [<string: missing skill or requirement 1>, ...],
  "required_qualifications": [<string: mandatory requirement 1>, ...],
  "preferred_qualifications": [<string: preferred requirement 1>, ...],
  "keywords": [<string: high-signal ATS keywords extracted from JD>]
}}
"""

        # 4. Invoke Ollama model
        logger.info(
            "Executing JD Analysis for job %d (%s) with candidate profile %d using model %s",
            job.id,
            job.title,
            profile.id,
            self.llm.model,
        )

        fallback_response = {
            "fit_score": 50.0,
            "fit_level": "medium",
            "summary": f"Automated analysis completed for {job.title} at {job.company}.",
            "role_summary": f"Role for {job.title}.",
            "key_responsibilities": [],
            "matched_skills": [s["name"] for s in ground_truth.get("skills", [])[:5]],
            "missing_skills": [],
            "required_qualifications": [],
            "preferred_qualifications": [],
            "keywords": job.skills_raw or [],
        }

        try:
            analysis_data = await self.llm.generate_structured_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                fallback_default=fallback_response,
            )
        except Exception as exc:
            logger.error("LLM analysis failed: %s", exc)
            raise AppError(f"Job description analysis failed: {exc}", status_code=502)

        # 5. Extract and normalize fields
        fit_score = float(analysis_data.get("fit_score", 50.0))
        fit_score = max(0.0, min(100.0, fit_score))

        fit_level = analysis_data.get("fit_level")
        if not fit_level or fit_level not in ["high", "medium", "low"]:
            fit_level = "high" if fit_score >= 75 else "medium" if fit_score >= 50 else "low"

        # 6. Save or update JobAnalysis record
        analysis = (
            db.query(JobAnalysis)
            .filter(JobAnalysis.job_id == job.id, JobAnalysis.candidate_profile_id == profile.id)
            .first()
        )
        if not analysis:
            analysis = (
                db.query(JobAnalysis)
                .filter(JobAnalysis.job_id == job.id)
                .first()
            )

        if not analysis:
            analysis = JobAnalysis(job_id=job.id, candidate_profile_id=profile.id)
            db.add(analysis)

        analysis.candidate_profile_id = profile.id
        analysis.fit_score = fit_score
        analysis.fit_level = fit_level
        analysis.summary = analysis_data.get("summary")
        analysis.role_summary = analysis_data.get("role_summary")
        analysis.key_responsibilities = analysis_data.get("key_responsibilities", [])
        analysis.matched_skills = analysis_data.get("matched_skills", [])
        analysis.missing_skills = analysis_data.get("missing_skills", [])
        analysis.required_qualifications = analysis_data.get("required_qualifications", [])
        analysis.preferred_qualifications = analysis_data.get("preferred_qualifications", [])
        analysis.keywords = analysis_data.get("keywords", [])
        analysis.model_used = self.llm.model
        analysis.status = "completed"
        analysis.analysis_metadata = {
            "model": self.llm.model,
            "provider": "ollama",
            "verified_facts_count": ground_truth["stats"]["total_verified_facts"],
        }

        # Also update job status to analyzing/reviewed
        if job.status == "discovered":
            job.status = "analyzed"

        # 7. Audit log
        audit = AuditLog(
            stage="jd_analysis",
            action="JOB_ANALYSIS_COMPLETED",
            message=f"Completed JD analysis for job {job.id} ({job.title} at {job.company}) with fit score {fit_score:.1f}% ({fit_level}).",
            payload={
                "job_id": job.id,
                "candidate_profile_id": profile.id,
                "fit_score": fit_score,
                "fit_level": fit_level,
                "model_used": self.llm.model,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(analysis)

        return analysis

    def get_job_analysis(self, db: Session, job_id: int) -> Optional[JobAnalysis]:
        """Retrieve the latest completed analysis for a job listing."""
        return (
            db.query(JobAnalysis)
            .filter(JobAnalysis.job_id == job_id)
            .order_by(JobAnalysis.updated_at.desc())
            .first()
        )


jd_analysis_service = JDAnalysisService()
