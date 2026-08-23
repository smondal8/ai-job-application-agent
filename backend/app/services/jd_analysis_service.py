from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError, BadRequestError, AppError
from app.core.logging import get_logger
from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.analysis import JobAnalysis
from app.models.audit import AuditLog
from app.services.profile_service import profile_service
from app.services.matching.deterministic import deterministic_matcher, DeterministicMatcher
from app.services.matching.semantic import semantic_matcher, SemanticMatcher

logger = get_logger("app.services.jd_analysis")
settings = get_settings()


class JDAnalysisService:
    """Orchestrates deterministic & LLM semantic matching for deep job description analysis."""

    def __init__(
        self,
        det_matcher: Optional[DeterministicMatcher] = None,
        sem_matcher: Optional[SemanticMatcher] = None,
    ):
        self.det_matcher = det_matcher or deterministic_matcher
        self.sem_matcher = sem_matcher or semantic_matcher

    async def analyze_job(
        self,
        db: Session,
        job_id: int,
        candidate_profile_id: Optional[int] = None,
        custom_instructions: Optional[str] = None,
    ) -> JobAnalysis:
        """Execute strict structured output pipeline for JD analysis and candidate matching."""
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
        candidate_skills = ground_truth.get("skills", [])

        # 3. Deterministic Matching Phase
        job_dict = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote_type": job.remote_type,
            "department": job.department,
            "skills_raw": job.skills_raw or [],
            "description_clean": job.description_clean,
            "description_raw": job.description_raw,
            "experience_years_min": job.experience_years_min,
            "experience_years_max": job.experience_years_max,
        }

        matched_det, missing_det, det_score = self.det_matcher.match_skills(
            candidate_skills=candidate_skills,
            job_skills_raw=job.skills_raw or [],
            job_description_text=job.description_clean or job.description_raw or job.title,
        )
        criteria_eval = self.det_matcher.evaluate_criteria(
            candidate_facts=ground_truth,
            job_data=job_dict,
        )

        # 4. Semantic Matching Phase (Local Ollama LLM with prompt injection defense)
        logger.info(
            "Running semantic matching for job %d (%s) with candidate %d using %s",
            job.id,
            job.title,
            profile.id,
            settings.OLLAMA_MODEL,
        )

        semantic_res = await self.sem_matcher.evaluate(
            job_data=job_dict,
            candidate_ground_truth_md=candidate_context_md,
            custom_instructions=custom_instructions,
        )

        sem_score = float(semantic_res.get("semantic_match_score", 50.0))

        # 5. Calculate Weighted Composite Fit Score & Recommendation
        # 40% deterministic keyword/criteria match + 60% semantic domain/experience reasoning
        composite_fit_score = round((0.40 * det_score) + (0.60 * sem_score), 1)
        composite_fit_score = max(0.0, min(100.0, composite_fit_score))

        fit_level = "high" if composite_fit_score >= 75.0 else "medium" if composite_fit_score >= 50.0 else "low"
        
        recommendation = semantic_res.get("recommendation")
        if not recommendation or recommendation not in ["strong_apply", "apply", "stretch", "skip"]:
            recommendation = (
                "strong_apply" if composite_fit_score >= 85.0
                else "apply" if composite_fit_score >= 70.0
                else "stretch" if composite_fit_score >= 50.0
                else "skip"
            )

        # Combine matched skills (union)
        combined_matched = sorted(list(set(matched_det + (semantic_res.get("matched_skills") or []))))
        combined_missing = sorted(list(set(missing_det + (semantic_res.get("missing_skills") or []))))

        # 6. Save or Update JobAnalysis in DB
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
        analysis.fit_score = composite_fit_score
        analysis.deterministic_score = det_score
        analysis.semantic_score = sem_score
        analysis.fit_level = fit_level
        analysis.recommendation = recommendation
        analysis.summary = semantic_res.get("semantic_match_reasoning") or f"Evaluated match for {job.title}."
        analysis.role_summary = semantic_res.get("role_summary")
        analysis.key_responsibilities = semantic_res.get("key_responsibilities", [])
        analysis.matched_skills = combined_matched
        analysis.missing_skills = combined_missing
        analysis.required_qualifications = semantic_res.get("required_qualifications", [])
        analysis.preferred_qualifications = semantic_res.get("preferred_qualifications", [])
        analysis.keywords = semantic_res.get("keywords", job.skills_raw or [])
        analysis.red_flags = semantic_res.get("red_flags", [])
        analysis.model_used = settings.OLLAMA_MODEL
        analysis.status = "completed"
        analysis.analysis_metadata = {
            "model": settings.OLLAMA_MODEL,
            "provider": "ollama",
            "deterministic_score": det_score,
            "semantic_score": sem_score,
            "criteria_eval": criteria_eval,
            "verified_facts_count": ground_truth["stats"]["total_verified_facts"],
        }

        # Update job status
        if job.status == "discovered":
            job.status = "analyzed"

        # 7. Audit Ledger
        audit = AuditLog(
            stage="jd_analysis",
            action="JOB_ANALYSIS_COMPLETED",
            message=f"Completed JD analysis for job {job.id} ({job.title} at {job.company}): Fit Score {composite_fit_score:.1f}% ({fit_level}, {recommendation}).",
            payload={
                "job_id": job.id,
                "candidate_profile_id": profile.id,
                "composite_fit_score": composite_fit_score,
                "deterministic_score": det_score,
                "semantic_score": sem_score,
                "recommendation": recommendation,
                "model_used": settings.OLLAMA_MODEL,
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

    def list_analyses(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        fit_level: Optional[str] = None,
        recommendation: Optional[str] = None,
    ) -> List[JobAnalysis]:
        """List job analyses paginated with optional filtering."""
        query = db.query(JobAnalysis)
        if fit_level and fit_level != "all":
            query = query.filter(JobAnalysis.fit_level == fit_level)
        if recommendation and recommendation != "all":
            query = query.filter(JobAnalysis.recommendation == recommendation)
        return query.order_by(JobAnalysis.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


jd_analysis_service = JDAnalysisService()
