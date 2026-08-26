from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError, BadRequestError, AppError
from app.core.logging import get_logger
from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.audit import AuditLog
from app.services.profile_service import profile_service
from app.services.jd_analysis_service import jd_analysis_service
from app.services.llm.ollama_service import ollama_service, OllamaLLMService
from app.services.tailoring.fact_registry import AtomicFactRegistry
from app.services.tailoring.prompts import PROMPT_VERSION, TAILORING_PROMPT_ID, build_traceable_tailoring_prompt
from app.services.tailoring.validator import traceability_validator, TraceabilityValidator, ValidationResult
from app.services.tailoring.compiler import resume_document_compiler, ResumeDocumentCompiler

logger = get_logger("app.services.tailoring.service")
settings = get_settings()


class ResumeTailoringService:
    """Orchestrates grounded resume tailoring with atomic source fact traceability and deterministic document compilation."""

    def __init__(
        self,
        llm_provider: Optional[OllamaLLMService] = None,
        validator: Optional[TraceabilityValidator] = None,
        compiler: Optional[ResumeDocumentCompiler] = None,
    ):
        self.llm = llm_provider or ollama_service
        self.validator = validator or traceability_validator
        self.compiler = compiler or resume_document_compiler

    async def tailor_application_materials(
        self,
        db: Session,
        job_id: int,
        candidate_profile_id: Optional[int] = None,
        tone: str = "professional",
        target_role_title: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        auto_regenerate_on_untraced: bool = True,
    ) -> TailoredResume:
        """Generate tailored resume and cover letter strictly grounded in verified candidate facts."""
        # 1. Fetch Job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found.")

        # 2. Resolve Candidate Profile
        profile: Optional[CandidateProfile] = None
        if candidate_profile_id:
            profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_profile_id).first()
        else:
            profile = db.query(CandidateProfile).order_by(CandidateProfile.id.asc()).first()

        if not profile:
            raise BadRequestError("No candidate profile found. Create and verify a profile first.")

        # 3. Retrieve verified ground truth context and build AtomicFactRegistry
        ground_truth = profile_service.get_verified_ground_truth_context(db, profile.id)
        fact_registry = AtomicFactRegistry.from_ground_truth(ground_truth)

        # 4. Resolve JobAnalysis (or run analysis if missing)
        analysis = (
            db.query(JobAnalysis)
            .filter(JobAnalysis.job_id == job.id, JobAnalysis.candidate_profile_id == profile.id)
            .order_by(JobAnalysis.updated_at.desc())
            .first()
        )
        if not analysis:
            analysis = await jd_analysis_service.analyze_job(
                db=db,
                job_id=job.id,
                candidate_profile_id=profile.id,
            )

        job_dict = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote_type": job.remote_type,
            "department": job.department,
            "skills_raw": job.skills_raw or [],
        }
        analysis_dict = {
            "role_summary": analysis.role_summary or "",
            "key_responsibilities": analysis.key_responsibilities or [],
            "matched_skills": analysis.matched_skills or [],
            "keywords": analysis.keywords or [],
            "summary": analysis.summary or "",
        }

        # 5. Build prompt
        system_prompt, user_prompt = build_traceable_tailoring_prompt(
            job_dict=job_dict,
            job_analysis_dict=analysis_dict,
            fact_registry_text=fact_registry.format_for_prompt(),
            tone=tone,
            target_role_title=target_role_title,
            custom_instructions=custom_instructions,
        )

        # 6. Execute LLM structured generation
        logger.info(
            "Invoking Ollama for grounded resume tailoring (job=%d, candidate=%d, prompt_version=%s)",
            job.id,
            profile.id,
            PROMPT_VERSION,
        )

        fallback_highlights = []
        for exp in ground_truth.get("experiences", []):
            exp_id = exp.get("id", "1")
            company_name = exp.get("company", "Company")
            pos = exp.get("position", "Engineer")
            loc = exp.get("location")
            h_objs = []

            raw_hl = exp.get("highlights") or []
            if not raw_hl and exp.get("description"):
                desc_text = str(exp["description"]).strip()
                desc_lines = [line.strip().lstrip("•-* ").strip() for line in desc_text.split("\n") if line.strip()]
                raw_hl = desc_lines if desc_lines else [desc_text]

            for h_idx, h in enumerate(raw_hl):
                h_text = h.get("text", "") if isinstance(h, dict) else str(h)
                if h_text and h_text.strip():
                    h_objs.append({
                        "text": h_text.strip(),
                        "source_fact_ids": [f"exp:{exp_id}:h{h_idx}"],
                    })

            if not h_objs:
                h_objs.append({
                    "text": f"Served as {pos} at {company_name}.",
                    "source_fact_ids": [f"exp:{exp_id}"],
                })

            fallback_highlights.append({
                "company": company_name,
                "position": pos,
                "location": loc,
                "start_date": exp.get("start_date", ""),
                "end_date": exp.get("end_date"),
                "is_current": exp.get("is_current", False),
                "tailored_highlights": h_objs,
            })

        fallback_skills = []
        matched_set = set(analysis_dict.get("matched_skills", []))
        all_skills = ground_truth.get("skills", [])
        sorted_skills = sorted(
            all_skills,
            key=lambda s: 0 if s.get("name", "") in matched_set else 1
        )
        for sk in sorted_skills[:15]:
            sk_name = sk.get("name", "")
            sk_id = sk.get("id") or sk_name.lower().replace(" ", "_")
            fallback_skills.append({
                "name": sk_name,
                "category": sk.get("category"),
                "source_fact_ids": [f"skill:{sk_id}"],
            })

        cand_summary = profile.summary or ground_truth.get("candidate", {}).get("summary") or ""
        summary_text_val = (
            cand_summary.strip()
            if cand_summary.strip()
            else f"{profile.headline or 'Experienced Professional'} with proven background aligned with {job.title} at {job.company}."
        )
        summary_fids = [f"profile:{profile.id}:summary"] if cand_summary.strip() else [f"profile:{profile.id}:headline"]

        fallback_tailored: Dict[str, Any] = {
            "tailored_summary": {
                "text": summary_text_val,
                "source_fact_ids": summary_fids,
            },
            "tailored_experience": fallback_highlights,
            "highlighted_skills": fallback_skills,
            "cover_letter_paragraphs": [
                {
                    "paragraph_type": "opening",
                    "text": f"I am writing to express my strong interest in the {job.title} role at {job.company}.",
                    "source_fact_ids": [f"profile:{profile.id}:headline"],
                },
                {
                    "paragraph_type": "body_skills",
                    "text": f"My technical background and verified accomplishments directly align with your requirements.",
                    "source_fact_ids": [s["source_fact_ids"][0] for s in fallback_skills[:3]] if fallback_skills else [f"profile:{profile.id}:headline"],
                },
                {
                    "paragraph_type": "closing",
                    "text": f"Thank you for your consideration. I look forward to discussing how I can contribute to {job.company}.",
                    "source_fact_ids": [f"profile:{profile.id}:headline"],
                },
            ],
            "diff_summary": "Prioritized core verified skills and accomplishments matching target role.",
        }

        raw_llm_json = await self.llm.generate_structured_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            fallback_default=fallback_tailored,
        )

        # Normalize LLM structured response keys
        if not isinstance(raw_llm_json, dict):
            raw_llm_json = fallback_tailored

        if "summary" in raw_llm_json and "tailored_summary" not in raw_llm_json:
            raw_llm_json["tailored_summary"] = raw_llm_json["summary"]
        if "experience" in raw_llm_json and "tailored_experience" not in raw_llm_json:
            raw_llm_json["tailored_experience"] = raw_llm_json["experience"]
        if "work_experience" in raw_llm_json and "tailored_experience" not in raw_llm_json:
            raw_llm_json["tailored_experience"] = raw_llm_json["work_experience"]
        if "skills" in raw_llm_json and "highlighted_skills" not in raw_llm_json:
            raw_llm_json["highlighted_skills"] = raw_llm_json["skills"]
        if "technical_skills" in raw_llm_json and "highlighted_skills" not in raw_llm_json:
            raw_llm_json["highlighted_skills"] = raw_llm_json["technical_skills"]

        # Ensure tailored_experience is not empty and each experience has highlights
        if not raw_llm_json.get("tailored_experience"):
            raw_llm_json["tailored_experience"] = fallback_highlights
        else:
            normalized_exp = []
            for item in raw_llm_json["tailored_experience"]:
                if not isinstance(item, dict):
                    continue
                c_name = item.get("company") or item.get("company_name") or "Company"
                pos = item.get("position") or item.get("role") or item.get("title") or "Position"
                st = item.get("start_date") or ""
                ed = item.get("end_date")
                is_curr = item.get("is_current", False)
                loc = item.get("location")

                hl_list = item.get("tailored_highlights") or item.get("highlights") or item.get("bullets") or item.get("bullet_points") or []
                hl_normalized = []
                for h_idx, h in enumerate(hl_list):
                    if isinstance(h, dict):
                        h_text = h.get("text", "")
                        h_fids = h.get("source_fact_ids") or []
                        if h_text and h_text.strip():
                            hl_normalized.append({"text": h_text.strip(), "source_fact_ids": h_fids})
                    elif isinstance(h, str) and h.strip():
                        hl_normalized.append({"text": h.strip(), "source_fact_ids": []})

                if not hl_normalized and item.get("description"):
                    hl_normalized.append({"text": str(item["description"]).strip(), "source_fact_ids": []})

                normalized_exp.append({
                    "company": c_name,
                    "position": pos,
                    "location": loc,
                    "start_date": st,
                    "end_date": ed,
                    "is_current": is_curr,
                    "tailored_highlights": hl_normalized,
                })
            raw_llm_json["tailored_experience"] = normalized_exp if normalized_exp else fallback_highlights

        # Ensure highlighted_skills is not empty
        if not raw_llm_json.get("highlighted_skills"):
            raw_llm_json["highlighted_skills"] = fallback_skills
        else:
            normalized_skills = []
            for sk in raw_llm_json["highlighted_skills"]:
                if isinstance(sk, dict):
                    s_name = sk.get("name", "")
                    s_fids = sk.get("source_fact_ids") or []
                    s_cat = sk.get("category")
                    if s_name and s_name.strip():
                        normalized_skills.append({"name": s_name.strip(), "category": s_cat, "source_fact_ids": s_fids})
                elif isinstance(sk, str) and sk.strip():
                    normalized_skills.append({"name": sk.strip(), "source_fact_ids": [f"skill:{sk.strip().lower().replace(' ', '_')}"]})
            raw_llm_json["highlighted_skills"] = normalized_skills if normalized_skills else fallback_skills

        # Ensure tailored_summary is not empty
        if not raw_llm_json.get("tailored_summary"):
            raw_llm_json["tailored_summary"] = fallback_tailored["tailored_summary"]

        # Ensure cover_letter_paragraphs is populated
        if not raw_llm_json.get("cover_letter_paragraphs"):
            raw_llm_json["cover_letter_paragraphs"] = fallback_tailored["cover_letter_paragraphs"]

        # 7. Traceability Validation
        validation_result = self.validator.validate(
            tailored_data=raw_llm_json,
            fact_registry=fact_registry,
        )

        # 8. Automatic Regeneration on Untraced Claims (if enabled)
        if not validation_result.is_valid and auto_regenerate_on_untraced and validation_result.untraced_claims:
            logger.warning(
                "Tailoring output had %d untraced claims. Triggering corrective regeneration.",
                len(validation_result.untraced_claims),
            )
            feedback_lines = ["\n### CORRECTION REQUIRED: UNTRACED CLAIMS DETECTED"]
            for uc in validation_result.untraced_claims[:3]:
                feedback_lines.append(f"- Section '{uc.section}': \"{uc.text}\" (Reason: {uc.reason})")
            feedback_lines.append("Please rewrite strictly using ONLY verified fact IDs from the registry provided above.")

            retry_prompt = user_prompt + "\n" + "\n".join(feedback_lines)
            retry_json = await self.llm.generate_structured_json(
                prompt=retry_prompt,
                system_prompt=system_prompt,
                fallback_default=raw_llm_json,
            )
            retry_validation = self.validator.validate(
                tailored_data=retry_json,
                fact_registry=fact_registry,
            )
            if retry_validation.traceability_score >= validation_result.traceability_score:
                raw_llm_json = retry_json
                validation_result = retry_validation

        # 9. Deterministic Document Compilation
        candidate_info = ground_truth.get("candidate", {})
        educations = ground_truth.get("educations", [])
        projects = ground_truth.get("projects", [])

        compiled_md = self.compiler.compile_markdown(
            candidate_info=candidate_info,
            tailored_data=raw_llm_json,
            educations=educations,
            projects=projects,
            include_traceability_annotations=False,
        )
        compiled_text = self.compiler.compile_text(
            candidate_info=candidate_info,
            tailored_data=raw_llm_json,
            educations=educations,
            projects=projects,
        )
        compiled_html = self.compiler.compile_html(
            candidate_info=candidate_info,
            tailored_data=raw_llm_json,
            educations=educations,
            projects=projects,
        )
        compiled_cover_letter = self.compiler.compile_cover_letter(
            candidate_info=candidate_info,
            job_info=job_dict,
            tailored_data=raw_llm_json,
        )

        # 10. Persist Document to Local Storage
        storage_dir = Path(settings.STORAGE_DIR) / "tailored_resumes"
        storage_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"tailored_job_{job.id}_profile_{profile.id}.md"
        file_path = storage_dir / file_name
        file_path.write_text(compiled_md, encoding="utf-8")

        # 11. Extract flat list of highlighted skills and experience for DB
        skills_flat = []
        for sk in raw_llm_json.get("highlighted_skills", []):
            if isinstance(sk, dict):
                skills_flat.append(sk.get("name", ""))
            elif isinstance(sk, str):
                skills_flat.append(sk)
        skills_flat = [s for s in skills_flat if s]

        summary_text_val = ""
        summary_obj = raw_llm_json.get("tailored_summary")
        if isinstance(summary_obj, dict):
            summary_text_val = summary_obj.get("text", "")
        elif isinstance(summary_obj, str):
            summary_text_val = summary_obj

        # 12. Save or Update TailoredResume in Database
        tailored_record = (
            db.query(TailoredResume)
            .filter(TailoredResume.job_id == job.id, TailoredResume.candidate_profile_id == profile.id)
            .first()
        )
        if not tailored_record:
            tailored_record = TailoredResume(
                job_id=job.id,
                candidate_profile_id=profile.id,
            )
            db.add(tailored_record)

        tailored_record.job_analysis_id = analysis.id
        tailored_record.prompt_version = PROMPT_VERSION
        tailored_record.model_used = settings.OLLAMA_MODEL
        tailored_record.tailored_summary = summary_text_val
        tailored_record.tailored_experience = raw_llm_json.get("tailored_experience", [])
        tailored_record.highlighted_skills = skills_flat
        tailored_record.cover_letter = compiled_cover_letter
        tailored_record.cover_letter_paragraphs = raw_llm_json.get("cover_letter_paragraphs", [])
        tailored_record.diff_summary = raw_llm_json.get("diff_summary", "")
        tailored_record.compiled_markdown = compiled_md
        tailored_record.compiled_text = compiled_text
        tailored_record.compiled_html = compiled_html
        tailored_record.markdown_content = compiled_md
        tailored_record.file_path = str(file_path)
        tailored_record.traceability_matrix = validation_result.traceability_matrix
        tailored_record.validation_status = validation_result.status
        tailored_record.validation_details = {
            "is_valid": validation_result.is_valid,
            "traceability_score": validation_result.traceability_score,
            "total_claims": validation_result.total_claims_count,
            "verified_claims": validation_result.verified_claims_count,
            "untraced_claims": [u.model_dump() for u in validation_result.untraced_claims],
            "warnings": validation_result.warnings,
        }
        tailored_record.generation_metadata = {
            "prompt_version": PROMPT_VERSION,
            "prompt_template_id": TAILORING_PROMPT_ID,
            "model": settings.OLLAMA_MODEL,
            "tone": tone,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        tailored_record.status = "ready_for_review"

        # Update Job status
        if job.status in ["discovered", "analyzed"]:
            job.status = "tailored"

        # 13. Audit Logging
        audit = AuditLog(
            stage="resume_tailoring",
            action="RESUME_TAILORED_GROUNDED",
            message=f"Generated grounded tailored application for job {job.id} ({job.title} at {job.company}) with {validation_result.traceability_score:.1f}% fact traceability ({validation_result.status}).",
            payload={
                "job_id": job.id,
                "candidate_profile_id": profile.id,
                "prompt_version": PROMPT_VERSION,
                "model_used": settings.OLLAMA_MODEL,
                "traceability_score": validation_result.traceability_score,
                "validation_status": validation_result.status,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(tailored_record)

        return tailored_record

    def get_tailored_resume(self, db: Session, job_id: int) -> Optional[TailoredResume]:
        """Retrieve latest tailored resume for a specific job."""
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
        status: Optional[str] = None,
        validation_status: Optional[str] = None,
    ) -> List[TailoredResume]:
        """List tailored resumes with pagination and status filters."""
        query = db.query(TailoredResume)
        if status and status != "all":
            query = query.filter(TailoredResume.status == status)
        if validation_status and validation_status != "all":
            query = query.filter(TailoredResume.validation_status == validation_status)
        return query.order_by(TailoredResume.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    def approve_tailored_resume(
        self,
        db: Session,
        tailored_id: int,
        approver_notes: Optional[str] = None,
    ) -> TailoredResume:
        """Mark tailored application approved by human reviewer."""
        record = db.query(TailoredResume).filter(TailoredResume.id == tailored_id).first()
        if not record:
            raise NotFoundError(f"Tailored resume ID {tailored_id} not found.")

        record.status = "approved"
        record.human_approved_at = datetime.now(timezone.utc)
        record.human_approver_notes = approver_notes

        audit = AuditLog(
            stage="resume_tailoring",
            action="RESUME_APPROVED",
            message=f"Human approved tailored resume ID {tailored_id} for job {record.job_id}.",
            payload={"tailored_id": tailored_id, "job_id": record.job_id, "notes": approver_notes},
        )
        db.add(audit)
        db.commit()
        db.refresh(record)
        return record


resume_tailoring_service = ResumeTailoringService()
