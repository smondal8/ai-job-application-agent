import hashlib
import json
from typing import Any, Dict, Optional

from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.resume import TailoredResume


def _normalize_json_for_hashing(obj: Any) -> str:
    """Deterministic JSON serializer with sorted keys and compact separators."""
    if obj is None:
        return ""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def compute_job_hash(job: Optional[Job]) -> str:
    """Compute cryptographic SHA-256 hash of immutable job specification inputs."""
    if not job:
        return hashlib.sha256(b"job:none").hexdigest()

    data = {
        "id": job.id,
        "title": (job.title or "").strip().lower(),
        "company": (job.company or "").strip().lower(),
        "description": (job.description_clean or job.description_raw or "").strip(),
        "location": (job.location or "").strip().lower(),
        "remote_type": (job.remote_type or "").strip().lower(),
        "url": (job.url or "").strip(),
    }
    raw_str = _normalize_json_for_hashing(data)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def compute_candidate_hash(profile: Optional[CandidateProfile]) -> str:
    """Compute cryptographic SHA-256 hash of verified candidate ground truth profile."""
    if not profile:
        return hashlib.sha256(b"candidate:none").hexdigest()

    # Collect experiences
    exps = []
    for e in getattr(profile, "experiences", []):
        exps.append({
            "company": e.company,
            "position": e.position,
            "highlights": sorted(e.highlights or []),
            "skills": sorted(e.skills_used or []),
            "is_verified": e.is_verified,
        })
    exps.sort(key=lambda x: (x["company"], x["position"]))

    # Collect skills
    skills = []
    for s in getattr(profile, "skills", []):
        skills.append({
            "name": s.name.lower(),
            "category": s.category,
            "is_verified": s.is_verified,
        })
    skills.sort(key=lambda x: x["name"])

    # Collect educations
    edus = []
    for ed in getattr(profile, "educations", []):
        edus.append({
            "institution": ed.institution,
            "degree": ed.degree,
            "is_verified": ed.is_verified,
        })
    edus.sort(key=lambda x: (x["institution"], x["degree"]))

    data = {
        "id": profile.id,
        "full_name": profile.full_name,
        "email": profile.email,
        "is_verified": profile.is_verified,
        "experiences": exps,
        "skills": skills,
        "educations": edus,
    }
    raw_str = _normalize_json_for_hashing(data)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def compute_resume_hash(resume: Optional[TailoredResume]) -> str:
    """Compute cryptographic SHA-256 hash of tailored resume artifacts & fact matrix."""
    if not resume:
        return hashlib.sha256(b"resume:none").hexdigest()

    data = {
        "id": resume.id,
        "job_id": resume.job_id,
        "prompt_version": resume.prompt_version,
        "tailored_summary": (resume.tailored_summary or "").strip(),
        "tailored_experience": resume.tailored_experience or [],
        "highlighted_skills": sorted(resume.highlighted_skills or []),
        "cover_letter": (resume.cover_letter or "").strip(),
        "compiled_markdown": (resume.compiled_markdown or resume.markdown_content or "").strip(),
        "validation_status": resume.validation_status,
        "traceability_matrix": resume.traceability_matrix or {},
    }
    raw_str = _normalize_json_for_hashing(data)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def compute_answers_hash(answers_payload: Optional[Dict[str, Any]]) -> str:
    """Compute cryptographic SHA-256 hash of screening questions answers payload."""
    raw_str = _normalize_json_for_hashing(answers_payload or {})
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def generate_approval_token(
    application_id: int,
    job_hash: str,
    candidate_hash: str,
    resume_hash: str,
    answers_hash: str,
    approved_at_iso: str,
) -> str:
    """Generate cryptographic approval authorization token binding all material input hashes."""
    combined = f"app:{application_id}|job:{job_hash}|cand:{candidate_hash}|res:{resume_hash}|ans:{answers_hash}|at:{approved_at_iso}"
    digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return f"auth_app_{application_id}_{digest[:32]}"
