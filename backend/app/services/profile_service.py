from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.errors import NotFoundError, BadRequestError
from app.core.logging import get_logger
from app.models.candidate import (
    CandidateProfile,
    WorkExperience,
    Education,
    CandidateSkill,
    Project,
    RawResumeImport,
)
from app.models.audit import AuditLog
from app.services.file_storage_service import storage_service
from app.services.resume_parser_service import resume_parser

logger = get_logger("app.services.profile")


class CandidateProfileService:
    """Authoritative Candidate Profile & Master Resume Service Boundary.
    
    GUARANTEES:
    1. Future LLM modules retrieve ONLY verified candidate facts.
    2. Imported resume text is untrusted until explicitly verified by the user.
    3. Never invents missing facts.
    4. Never logs full resume contents.
    5. Records comprehensive audit trail for all changes.
    """

    def _log_audit(
        self,
        db: Session,
        action: str,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
        level: str = "info",
    ) -> None:
        """Create an audit log record without leaking full text/PII bodies."""
        audit = AuditLog(
            application_id=None,
            stage="profile_management",
            action=action,
            level=level,
            message=message,
            payload=payload or {},
        )
        db.add(audit)
        # We do not commit here; commit happens with parent transaction

    def get_or_create_primary_profile(self, db: Session) -> CandidateProfile:
        """Fetch primary profile or initialize a clean one."""
        profile = db.query(CandidateProfile).order_by(CandidateProfile.id.asc()).first()
        if not profile:
            profile = CandidateProfile(
                full_name="Candidate Name",
                email="candidate@example.com",
                headline="Software Engineer",
                summary="",
                is_verified=False,
            )
            db.add(profile)
            self._log_audit(
                db,
                action="PROFILE_INITIALIZED",
                message="Initialized default master candidate profile.",
                payload={"profile_id": 1, "is_verified": False},
            )
            db.commit()
            db.refresh(profile)
        return profile

    def get_profile_by_id(self, db: Session, profile_id: int) -> CandidateProfile:
        """Get profile by ID."""
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
        if not profile:
            raise NotFoundError(f"Candidate profile with id {profile_id} not found.")
        return profile

    def update_profile(
        self, db: Session, profile_id: int, profile_data: Dict[str, Any]
    ) -> CandidateProfile:
        """Update candidate basic profile fields."""
        profile = self.get_profile_by_id(db, profile_id)
        
        updatable_fields = [
            "full_name", "email", "phone", "location", "headline",
            "summary", "website", "linkedin_url", "github_url", "portfolio_url"
        ]
        
        updated_keys = []
        for field in updatable_fields:
            if field in profile_data and profile_data[field] is not None:
                setattr(profile, field, profile_data[field])
                updated_keys.append(field)

        self._log_audit(
            db,
            action="PROFILE_UPDATED",
            message=f"Updated candidate profile fields: {', '.join(updated_keys)}",
            payload={"profile_id": profile_id, "updated_fields": updated_keys},
        )
        db.commit()
        db.refresh(profile)
        return profile

    def verify_profile(
        self, db: Session, profile_id: int, verify_all_children: bool = False
    ) -> CandidateProfile:
        """Verify candidate profile and optionally all child facts."""
        profile = self.get_profile_by_id(db, profile_id)
        profile.is_verified = True
        profile.verified_at = datetime.now(timezone.utc)

        verified_counts = {"experiences": 0, "educations": 0, "skills": 0, "projects": 0}
        if verify_all_children:
            for exp in profile.experiences:
                exp.is_verified = True
                verified_counts["experiences"] += 1
            for edu in profile.educations:
                edu.is_verified = True
                verified_counts["educations"] += 1
            for skill in profile.skills:
                skill.is_verified = True
                verified_counts["skills"] += 1
            for proj in profile.projects:
                proj.is_verified = True
                verified_counts["projects"] += 1

        self._log_audit(
            db,
            action="PROFILE_VERIFIED",
            message="Candidate profile verified and approved for LLM ground truth.",
            payload={
                "profile_id": profile_id,
                "verified_all_children": verify_all_children,
                "counts": verified_counts,
            },
        )
        db.commit()
        db.refresh(profile)
        return profile

    # --- Work Experience Management ---

    def add_experience(
        self, db: Session, profile_id: int, exp_data: Dict[str, Any]
    ) -> WorkExperience:
        self.get_profile_by_id(db, profile_id)
        exp = WorkExperience(profile_id=profile_id, **exp_data)
        db.add(exp)
        self._log_audit(
            db,
            action="EXPERIENCE_ADDED",
            message=f"Added work experience at {exp.company}",
            payload={"profile_id": profile_id, "company": exp.company, "position": exp.position},
        )
        db.commit()
        db.refresh(exp)
        return exp

    def update_experience(
        self, db: Session, exp_id: int, exp_data: Dict[str, Any]
    ) -> WorkExperience:
        exp = db.query(WorkExperience).filter(WorkExperience.id == exp_id).first()
        if not exp:
            raise NotFoundError(f"Work experience with id {exp_id} not found.")
        
        for k, v in exp_data.items():
            if hasattr(exp, k) and v is not None:
                setattr(exp, k, v)

        self._log_audit(
            db,
            action="EXPERIENCE_UPDATED",
            message=f"Updated experience {exp_id} at {exp.company}",
            payload={"experience_id": exp_id, "company": exp.company},
        )
        db.commit()
        db.refresh(exp)
        return exp

    def delete_experience(self, db: Session, exp_id: int) -> None:
        exp = db.query(WorkExperience).filter(WorkExperience.id == exp_id).first()
        if not exp:
            raise NotFoundError(f"Work experience with id {exp_id} not found.")
        company = exp.company
        db.delete(exp)
        self._log_audit(
            db,
            action="EXPERIENCE_DELETED",
            message=f"Deleted experience {exp_id} ({company})",
            payload={"experience_id": exp_id},
        )
        db.commit()

    def verify_experience(self, db: Session, exp_id: int, verified: bool = True) -> WorkExperience:
        exp = db.query(WorkExperience).filter(WorkExperience.id == exp_id).first()
        if not exp:
            raise NotFoundError(f"Work experience with id {exp_id} not found.")
        exp.is_verified = verified
        self._log_audit(
            db,
            action="EXPERIENCE_VERIFIED" if verified else "EXPERIENCE_UNVERIFIED",
            message=f"Toggled verification for experience {exp_id} to {verified}",
            payload={"experience_id": exp_id, "verified": verified},
        )
        db.commit()
        db.refresh(exp)
        return exp

    # --- Education Management ---

    def add_education(
        self, db: Session, profile_id: int, edu_data: Dict[str, Any]
    ) -> Education:
        self.get_profile_by_id(db, profile_id)
        edu = Education(profile_id=profile_id, **edu_data)
        db.add(edu)
        self._log_audit(
            db,
            action="EDUCATION_ADDED",
            message=f"Added education credential at {edu.institution}",
            payload={"profile_id": profile_id, "institution": edu.institution, "degree": edu.degree},
        )
        db.commit()
        db.refresh(edu)
        return edu

    def update_education(
        self, db: Session, edu_id: int, edu_data: Dict[str, Any]
    ) -> Education:
        edu = db.query(Education).filter(Education.id == edu_id).first()
        if not edu:
            raise NotFoundError(f"Education with id {edu_id} not found.")
        for k, v in edu_data.items():
            if hasattr(edu, k) and v is not None:
                setattr(edu, k, v)
        db.commit()
        db.refresh(edu)
        return edu

    def delete_education(self, db: Session, edu_id: int) -> None:
        edu = db.query(Education).filter(Education.id == edu_id).first()
        if not edu:
            raise NotFoundError(f"Education with id {edu_id} not found.")
        db.delete(edu)
        db.commit()

    def verify_education(self, db: Session, edu_id: int, verified: bool = True) -> Education:
        edu = db.query(Education).filter(Education.id == edu_id).first()
        if not edu:
            raise NotFoundError(f"Education with id {edu_id} not found.")
        edu.is_verified = verified
        db.commit()
        db.refresh(edu)
        return edu

    # --- Skills Management ---

    def add_skill(self, db: Session, profile_id: int, skill_data: Dict[str, Any]) -> CandidateSkill:
        self.get_profile_by_id(db, profile_id)
        skill = CandidateSkill(profile_id=profile_id, **skill_data)
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill

    def add_skills_bulk(
        self, db: Session, profile_id: int, skills_list: List[Dict[str, Any]]
    ) -> List[CandidateSkill]:
        self.get_profile_by_id(db, profile_id)
        created_skills = []
        for s_data in skills_list:
            if s_data.get("name"):
                skill = CandidateSkill(profile_id=profile_id, **s_data)
                db.add(skill)
                created_skills.append(skill)
        self._log_audit(
            db,
            action="SKILLS_BULK_ADDED",
            message=f"Added {len(created_skills)} skills to candidate profile.",
            payload={"profile_id": profile_id, "count": len(created_skills)},
        )
        db.commit()
        return created_skills

    def delete_skill(self, db: Session, skill_id: int) -> None:
        skill = db.query(CandidateSkill).filter(CandidateSkill.id == skill_id).first()
        if not skill:
            raise NotFoundError(f"Skill with id {skill_id} not found.")
        db.delete(skill)
        db.commit()

    def verify_skill(self, db: Session, skill_id: int, verified: bool = True) -> CandidateSkill:
        skill = db.query(CandidateSkill).filter(CandidateSkill.id == skill_id).first()
        if not skill:
            raise NotFoundError(f"Skill with id {skill_id} not found.")
        skill.is_verified = verified
        db.commit()
        db.refresh(skill)
        return skill

    # --- Projects Management ---

    def add_project(self, db: Session, profile_id: int, proj_data: Dict[str, Any]) -> Project:
        self.get_profile_by_id(db, profile_id)
        proj = Project(profile_id=profile_id, **proj_data)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        return proj

    def update_project(self, db: Session, proj_id: int, proj_data: Dict[str, Any]) -> Project:
        proj = db.query(Project).filter(Project.id == proj_id).first()
        if not proj:
            raise NotFoundError(f"Project with id {proj_id} not found.")
        for k, v in proj_data.items():
            if hasattr(proj, k) and v is not None:
                setattr(proj, k, v)
        db.commit()
        db.refresh(proj)
        return proj

    def delete_project(self, db: Session, proj_id: int) -> None:
        proj = db.query(Project).filter(Project.id == proj_id).first()
        if not proj:
            raise NotFoundError(f"Project with id {proj_id} not found.")
        db.delete(proj)
        db.commit()

    def verify_project(self, db: Session, proj_id: int, verified: bool = True) -> Project:
        proj = db.query(Project).filter(Project.id == proj_id).first()
        if not proj:
            raise NotFoundError(f"Project with id {proj_id} not found.")
        proj.is_verified = verified
        db.commit()
        db.refresh(proj)
        return proj

    # --- Raw Ingestion Subsystem ---

    def import_raw_resume_file(
        self,
        db: Session,
        filename: str,
        content_bytes: bytes,
        mime_type: str,
        profile_id: Optional[int] = None,
    ) -> RawResumeImport:
        """Securely store raw file and parse draft untrusted facts."""
        file_path, file_hash, size_bytes = storage_service.save_resume_file(
            filename=filename, content_bytes=content_bytes, mime_type=mime_type
        )
        
        # Format-aware extraction: safely parses DOCX, PDF, JSON, and Markdown binary/text
        clean_extracted_text, parsed_draft = resume_parser.parse_file_bytes(
            content_bytes=content_bytes, filename=filename, mime_type=mime_type
        )

        raw_import = RawResumeImport(
            profile_id=profile_id,
            filename=filename,
            file_path=file_path,
            file_hash=file_hash,
            file_size_bytes=size_bytes,
            mime_type=mime_type,
            raw_text=clean_extracted_text,
            parsed_data=parsed_draft,
            status="parsed",
        )
        db.add(raw_import)
        self._log_audit(
            db,
            action="RAW_RESUME_IMPORTED",
            message=f"Imported untrusted resume file '{filename}' (sha256={file_hash[:12]})",
            payload={"filename": filename, "file_hash": file_hash, "size_bytes": size_bytes},
        )
        db.commit()
        db.refresh(raw_import)
        return raw_import

    def import_raw_resume_text(
        self,
        db: Session,
        raw_text: str,
        label: str = "Pasted Resume Text",
        profile_id: Optional[int] = None,
    ) -> RawResumeImport:
        """Ingest raw pasted resume string."""
        content_bytes = raw_text.encode("utf-8")
        filename = f"{label.lower().replace(' ', '_')}.txt"
        return self.import_raw_resume_file(
            db=db,
            filename=filename,
            content_bytes=content_bytes,
            mime_type="text/plain",
            profile_id=profile_id,
        )

    def apply_raw_import_to_profile(
        self, db: Session, import_id: int, profile_id: int
    ) -> CandidateProfile:
        """Transfer extracted draft facts into candidate profile as UNVERIFIED entities."""
        raw_import = db.query(RawResumeImport).filter(RawResumeImport.id == import_id).first()
        if not raw_import:
            raise NotFoundError(f"Raw resume import with id {import_id} not found.")

        profile = self.get_profile_by_id(db, profile_id)
        draft = raw_import.parsed_data or {}

        # 1. Update basic profile info if draft contains data
        draft_profile = draft.get("profile") or {}
        if draft_profile.get("full_name") and draft_profile["full_name"] != "Imported Candidate":
            profile.full_name = draft_profile["full_name"]
        if draft_profile.get("email"):
            profile.email = draft_profile["email"]
        if draft_profile.get("phone") is not None:
            profile.phone = draft_profile["phone"]
        if draft_profile.get("location") is not None:
            profile.location = draft_profile["location"]
        if draft_profile.get("headline") is not None:
            profile.headline = draft_profile["headline"]
        if draft_profile.get("summary") is not None:
            profile.summary = draft_profile["summary"]
        if draft_profile.get("website") is not None:
            profile.website = draft_profile["website"]
        if draft_profile.get("linkedin_url") is not None:
            profile.linkedin_url = draft_profile["linkedin_url"]
        if draft_profile.get("github_url") is not None:
            profile.github_url = draft_profile["github_url"]
        if draft_profile.get("portfolio_url") is not None:
            profile.portfolio_url = draft_profile["portfolio_url"]

        # Note: Imported profile remains UNVERIFIED until user confirms
        profile.is_verified = False

        # 2. Add Experiences as unverified
        for exp in draft.get("experiences") or []:
            db.add(WorkExperience(
                profile_id=profile_id,
                company=exp.get("company", "Company"),
                position=exp.get("position", "Position"),
                location=exp.get("location"),
                start_date=exp.get("start_date", "2022"),
                end_date=exp.get("end_date"),
                is_current=exp.get("is_current", False),
                description=exp.get("description"),
                highlights=exp.get("highlights", []),
                skills_used=exp.get("skills_used", []),
                is_verified=False,
            ))

        # 3. Add Educations as unverified
        for edu in draft.get("educations") or []:
            db.add(Education(
                profile_id=profile_id,
                institution=edu.get("institution", "Institution"),
                degree=edu.get("degree", "Degree"),
                field_of_study=edu.get("field_of_study"),
                start_date=edu.get("start_date"),
                end_date=edu.get("end_date"),
                gpa=edu.get("gpa"),
                highlights=edu.get("highlights", []),
                is_verified=False,
            ))

        # 4. Add Skills as unverified
        for skill in draft.get("skills") or []:
            if skill.get("name"):
                db.add(CandidateSkill(
                    profile_id=profile_id,
                    name=skill["name"],
                    category=skill.get("category", "general"),
                    proficiency=skill.get("proficiency", "intermediate"),
                    is_verified=False,
                ))

        # 5. Add Projects as unverified
        for proj in draft.get("projects") or []:
            if proj.get("name"):
                db.add(Project(
                    profile_id=profile_id,
                    name=proj["name"],
                    description=proj.get("description"),
                    url=proj.get("url"),
                    highlights=proj.get("highlights", []),
                    technologies=proj.get("technologies", []),
                    is_verified=False,
                ))

        raw_import.status = "applied"
        self._log_audit(
            db,
            action="RAW_RESUME_APPLIED_TO_PROFILE",
            message=f"Transferred draft facts from import {import_id} into profile {profile_id}. Status: UNVERIFIED.",
            payload={"import_id": import_id, "profile_id": profile_id},
        )
        db.commit()
        db.refresh(profile)
        return profile

    # --- Authoritative LLM Context Service Boundary ---

    def get_verified_ground_truth_context(
        self, db: Session, profile_id: int
    ) -> Dict[str, Any]:
        """AUTHORITATIVE SERVICE BOUNDARY FOR DOWNSTREAM LLM MODULES.
        
        Strict Contract:
        - Retrieves ONLY facts where `is_verified == True`.
        - NEVER invents missing facts.
        - Unverified items are strictly excluded from the prompt context.
        """
        profile = self.get_profile_by_id(db, profile_id)

        # Strictly filter child entities where is_verified is True
        verified_experiences = (
            db.query(WorkExperience)
            .filter(WorkExperience.profile_id == profile_id, WorkExperience.is_verified == True)
            .order_by(WorkExperience.order_index)
            .all()
        )
        
        verified_educations = (
            db.query(Education)
            .filter(Education.profile_id == profile_id, Education.is_verified == True)
            .all()
        )

        verified_skills = (
            db.query(CandidateSkill)
            .filter(CandidateSkill.profile_id == profile_id, CandidateSkill.is_verified == True)
            .all()
        )

        verified_projects = (
            db.query(Project)
            .filter(Project.profile_id == profile_id, Project.is_verified == True)
            .all()
        )

        # Build clean ground-truth dictionary
        ground_truth: Dict[str, Any] = {
            "profile_id": profile.id,
            "profile_verified": profile.is_verified,
            "verified_at": profile.verified_at.isoformat() if profile.verified_at else None,
            "candidate": {
                "full_name": profile.full_name,
                "email": profile.email,
                "phone": profile.phone,
                "location": profile.location,
                "headline": profile.headline,
                "summary": profile.summary,
                "website": profile.website,
                "linkedin_url": profile.linkedin_url,
                "github_url": profile.github_url,
                "portfolio_url": profile.portfolio_url,
            },
            "experiences": [
                {
                    "id": exp.id,
                    "company": exp.company,
                    "position": exp.position,
                    "location": exp.location,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "is_current": exp.is_current,
                    "description": exp.description,
                    "highlights": exp.highlights or [],
                    "skills_used": exp.skills_used or [],
                }
                for exp in verified_experiences
            ],
            "educations": [
                {
                    "id": edu.id,
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "start_date": edu.start_date,
                    "end_date": edu.end_date,
                    "gpa": edu.gpa,
                    "highlights": edu.highlights or [],
                }
                for edu in verified_educations
            ],
            "skills": [
                {
                    "id": s.id,
                    "name": s.name,
                    "category": s.category,
                    "proficiency": s.proficiency,
                    "years_of_experience": s.years_of_experience,
                }
                for s in verified_skills
            ],
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "url": p.url,
                    "highlights": p.highlights or [],
                    "technologies": p.technologies or [],
                }
                for p in verified_projects
            ],
            "stats": {
                "verified_experiences_count": len(verified_experiences),
                "verified_educations_count": len(verified_educations),
                "verified_skills_count": len(verified_skills),
                "verified_projects_count": len(verified_projects),
                "total_verified_facts": (
                    len(verified_experiences)
                    + len(verified_educations)
                    + len(verified_skills)
                    + len(verified_projects)
                    + (1 if profile.is_verified else 0)
                ),
            },
        }

        # Format deterministic Markdown prompt context for downstream LLMs
        ground_truth["formatted_llm_prompt_context"] = self._format_markdown_prompt_context(ground_truth)

        self._log_audit(
            db,
            action="LLM_GROUND_TRUTH_CONTEXT_ACCESSED",
            message=f"Accessed verified ground truth facts for profile {profile_id}.",
            payload={
                "profile_id": profile_id,
                "verified_facts_count": ground_truth["stats"]["total_verified_facts"],
            },
        )
        db.commit()

        return ground_truth

    def _format_markdown_prompt_context(self, gt: Dict[str, Any]) -> str:
        """Format candidate ground truth into immutable markdown context."""
        c = gt["candidate"]
        lines = [
            "# AUTHORITATIVE CANDIDATE GROUND TRUTH (VERIFIED FACTS ONLY)",
            f"**Candidate Name**: {c['full_name']}",
            f"**Email**: {c['email']}",
        ]
        if c.get("phone"):
            lines.append(f"**Phone**: {c['phone']}")
        if c.get("location"):
            lines.append(f"**Location**: {c['location']}")
        if c.get("headline"):
            lines.append(f"**Headline**: {c['headline']}")
        if c.get("summary"):
            lines.append(f"\n### Professional Summary\n{c['summary']}")

        # Experiences
        if gt["experiences"]:
            lines.append("\n### Verified Work Experience")
            for exp in gt["experiences"]:
                end_str = "Present" if exp["is_current"] else (exp["end_date"] or "N/A")
                lines.append(f"\n#### {exp['position']} at {exp['company']} ({exp['start_date']} – {end_str})")
                if exp.get("location"):
                    lines.append(f"*Location*: {exp['location']}")
                if exp.get("description"):
                    lines.append(exp["description"])
                for bullet in exp.get("highlights", []):
                    lines.append(f"- {bullet}")
                if exp.get("skills_used"):
                    lines.append(f"*Technologies*: {', '.join(exp['skills_used'])}")

        # Skills
        if gt["skills"]:
            lines.append("\n### Verified Skills")
            categories: Dict[str, List[str]] = {}
            for s in gt["skills"]:
                cat = s["category"]
                categories.setdefault(cat, []).append(s["name"])
            for cat, skill_names in categories.items():
                lines.append(f"- **{cat.replace('_', ' ').title()}**: {', '.join(skill_names)}")

        # Education
        if gt["educations"]:
            lines.append("\n### Verified Education")
            for edu in gt["educations"]:
                date_str = f" ({edu['start_date']} – {edu['end_date']})" if edu.get("start_date") else ""
                lines.append(f"- **{edu['degree']}** in {edu.get('field_of_study') or 'General Studies'} – {edu['institution']}{date_str}")
                if edu.get("gpa"):
                    lines.append(f"  *GPA*: {edu['gpa']}")

        # Projects
        if gt["projects"]:
            lines.append("\n### Verified Projects")
            for p in gt["projects"]:
                lines.append(f"\n#### {p['name']}")
                if p.get("url"):
                    lines.append(f"*URL*: {p['url']}")
                if p.get("description"):
                    lines.append(p["description"])
                for h in p.get("highlights", []):
                    lines.append(f"- {h}")

        return "\n".join(lines)


profile_service = CandidateProfileService()
