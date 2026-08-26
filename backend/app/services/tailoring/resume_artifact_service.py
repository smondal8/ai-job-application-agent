from pathlib import Path
from typing import Any, List, Optional, Tuple
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.resume import TailoredResume
from app.services.tailoring.compiler import resume_document_compiler

logger = get_logger("app.services.tailoring.resume_artifact_service")


async def ensure_tailored_pdf_artifact(
    tailored_resume: Optional[TailoredResume],
    job_id: int,
    candidate_profile_id: int,
    settings: Any = None,
) -> Optional[Path]:
    """
    Ensures that a compiled, high-fidelity PDF artifact exists for the approved tailored resume.
    If the PDF file already exists on disk, returns it immediately.
    If not, compiles it deterministically from tailored_resume.compiled_html.
    Never modifies approved tailoring content or cryptographic hashes.
    """
    if not tailored_resume:
        return None

    if settings is None:
        settings = get_settings()

    storage_dir = Path(settings.STORAGE_DIR) / "tailored_resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)

    expected_pdf_path = storage_dir / f"tailored_job_{job_id}_profile_{candidate_profile_id}.pdf"

    # 1. Check if expected PDF already exists and is non-empty
    if expected_pdf_path.exists() and expected_pdf_path.stat().st_size > 0:
        return expected_pdf_path

    # 2. Check if tailored_resume.file_path points to an existing PDF
    if tailored_resume.file_path:
        fp = Path(tailored_resume.file_path)
        if fp.suffix.lower() == ".pdf" and fp.exists() and fp.stat().st_size > 0:
            return fp

    # 3. Retrieve or re-synthesize HTML content from tailored_resume
    html_content = tailored_resume.compiled_html
    if not html_content or not html_content.strip():
        candidate_info = {}
        if tailored_resume.candidate_profile:
            cand = tailored_resume.candidate_profile
            candidate_info = {
                "full_name": cand.full_name or "Candidate",
                "headline": cand.headline or "",
                "email": cand.email or "",
                "phone": cand.phone or "",
                "location": cand.location or "",
                "linkedin_url": cand.linkedin_url or "",
                "github_url": cand.github_url or "",
                "portfolio_url": cand.portfolio_url or "",
            }
        else:
            candidate_info = {"full_name": "Candidate"}

        tailored_data = {
            "tailored_summary": tailored_resume.tailored_summary or "",
            "highlighted_skills": tailored_resume.highlighted_skills or [],
            "tailored_experience": tailored_resume.tailored_experience or [],
        }

        html_content = resume_document_compiler.compile_html(
            candidate_info=candidate_info,
            tailored_data=tailored_data,
            educations=[],
        )

    # 4. Compile HTML to high-fidelity PDF
    try:
        await resume_document_compiler.compile_pdf_async(html_content, expected_pdf_path)
        if expected_pdf_path.exists() and expected_pdf_path.stat().st_size > 0:
            logger.info(f"Compiled approved PDF artifact for tailored resume #{tailored_resume.id} at {expected_pdf_path}")
            return expected_pdf_path
    except Exception as e:
        logger.error(f"Failed to compile PDF artifact for tailored resume #{tailored_resume.id}: {e}")

    return None


def resolve_best_upload_artifact(
    tailored_resume: Optional[TailoredResume],
    job_id: int,
    candidate_profile_id: int,
    accepted_extensions: Optional[List[str]] = None,
    settings: Any = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Selects the best available approved tailored resume artifact according to portal accepted extensions and priority:
    1. Approved PDF (.pdf)
    2. Approved DOCX (.docx)
    3. Never selects .md or .txt when the portal requires document formats.
    """
    if not tailored_resume:
        return None, "No tailored resume linked to application."

    if settings is None:
        settings = get_settings()

    storage_dir = Path(settings.STORAGE_DIR) / "tailored_resumes"
    pdf_path = storage_dir / f"tailored_job_{job_id}_profile_{candidate_profile_id}.pdf"
    docx_path = storage_dir / f"tailored_job_{job_id}_profile_{candidate_profile_id}.docx"

    norm_accepted = [e.lower() for e in accepted_extensions] if accepted_extensions else []

    # Priority 1: PDF artifact
    if not norm_accepted or ".pdf" in norm_accepted or "pdf" in norm_accepted or "*" in norm_accepted:
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            return pdf_path, None
        if tailored_resume.file_path:
            fp = Path(tailored_resume.file_path)
            if fp.suffix.lower() == ".pdf" and fp.exists() and fp.stat().st_size > 0:
                return fp, None

    # Priority 2: DOCX artifact
    if not norm_accepted or ".docx" in norm_accepted or "docx" in norm_accepted:
        if docx_path.exists() and docx_path.stat().st_size > 0:
            return docx_path, None

    return None, "Approved resume PDF is unavailable. Manual resume upload is required."
