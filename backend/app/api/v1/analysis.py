from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.schemas.analysis import (
    LLMStatusResponse,
    JobAnalysisRequest,
    JobAnalysisResponse,
)
from app.services.llm.ollama_service import ollama_service
from app.services.jd_analysis_service import jd_analysis_service

router = APIRouter(tags=["JD Analysis & Local LLM"])


@router.get("/llm/status", response_model=LLMStatusResponse)
async def get_llm_status():
    """Get connectivity, model availability, and latency of local Ollama LLM."""
    return await ollama_service.check_health()


@router.post("/jobs/{job_id}/analyze", response_model=JobAnalysisResponse, status_code=200)
async def analyze_job(
    job_id: int,
    payload: Optional[JobAnalysisRequest] = None,
    db: Session = Depends(get_db),
):
    """Analyze job description against verified candidate profile using local Ollama model."""
    candidate_profile_id = payload.candidate_profile_id if payload else None
    custom_instructions = payload.custom_instructions if payload else None

    analysis = await jd_analysis_service.analyze_job(
        db=db,
        job_id=job_id,
        candidate_profile_id=candidate_profile_id,
        custom_instructions=custom_instructions,
    )
    return analysis


@router.get("/jobs/{job_id}/analysis", response_model=JobAnalysisResponse)
def get_job_analysis(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve the latest structured analysis for a job listing."""
    analysis = jd_analysis_service.get_job_analysis(db=db, job_id=job_id)
    if not analysis:
        raise NotFoundError(f"No analysis found for job ID {job_id}. Run analysis first.")
    return analysis
