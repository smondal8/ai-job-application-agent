from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import (
    BadRequestError,
    NotFoundError,
    PipelineStageNotActiveError,
    DatabaseError,
)
from app.schemas.config import SystemConfigResponse, PipelineStageInfo

router = APIRouter(tags=["Configuration & Pipeline"])
settings = get_settings()


@router.get(
    "/config",
    response_model=SystemConfigResponse,
    summary="Get System Configuration",
    description="Returns public, sanitized configuration metadata and feature status.",
)
def get_system_config() -> SystemConfigResponse:
    config_dict = settings.get_public_config()
    return SystemConfigResponse(**config_dict)


@router.get(
    "/pipeline",
    response_model=List[PipelineStageInfo],
    summary="Get Pipeline Architecture Stages",
    description="Returns all 6 architecture stages and their active/planned status.",
)
def get_pipeline_stages() -> List[PipelineStageInfo]:
    stages = settings.get_public_config()["pipeline_stages"]
    return [PipelineStageInfo(**s) for s in stages]


@router.get(
    "/test-error",
    summary="Test Error Contract Dispatch",
    description="Endpoint for verifying and inspecting the unified API error contract.",
)
def test_error_contract(
    error_type: str = Query(
        "not_found",
        enum=["not_found", "bad_request", "pipeline_disabled", "database_error", "unhandled"],
        description="Type of error to trigger for testing error contract formatting",
    )
):
    if error_type == "not_found":
        raise NotFoundError("The requested test entity was not found.", details={"entity": "TestJob", "id": 999})
    elif error_type == "bad_request":
        raise BadRequestError("Invalid payload provided for test error simulation.", details={"field": "test_param"})
    elif error_type == "pipeline_disabled":
        raise PipelineStageNotActiveError(stage_name="Resume Tailoring Engine", planned_phase="Phase 4")
    elif error_type == "database_error":
        raise DatabaseError("Simulated database failure for testing error response contract.")
    elif error_type == "unhandled":
        # Simulate unhandled python exception
        raise ZeroDivisionError("Simulated unhandled zero division error")
    return {"message": "No error triggered"}
