from datetime import datetime, timezone
import traceback
from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger, request_id_ctx

logger = get_logger("app.errors")


class ErrorBody(BaseModel):
    """Standardized API Error Payload Schema."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Union[Dict[str, Any], List[Any], str]] = Field(
        default=None, description="Detailed validation errors or contextual diagnostic data"
    )
    request_id: Optional[str] = Field(default=None, description="Unique correlation ID for tracing")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of the error"
    )


class APIErrorResponse(BaseModel):
    """Top-level error response envelope conforming to API error contract."""
    error: ErrorBody


class AppException(Exception):
    """Base application exception for domain and business logic errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


AppError = AppException


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class BadRequestError(AppException):
    """Raised for malformed or invalid business requests."""

    def __init__(self, message: str = "Bad request", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ConflictError(AppException):
    """Raised when an operation conflicts with existing entity state."""

    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="CONFLICT_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class DatabaseError(AppException):
    """Raised when a database query or transaction fails."""

    def __init__(self, message: str = "Database operation failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class PipelineStageNotActiveError(AppException):
    """Raised when accessing a pipeline stage not enabled in the current phase."""

    def __init__(self, stage_name: str, planned_phase: str = "Phase 2+"):
        super().__init__(
            message=f"Pipeline stage '{stage_name}' is not enabled. Scheduled for {planned_phase}.",
            code="PIPELINE_STAGE_NOT_ACTIVE",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            details={"stage": stage_name, "planned_phase": planned_phase},
        )


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[Any] = None,
    req_id: Optional[str] = None,
) -> JSONResponse:
    """Helper to build consistent JSONResponse matching API error contract."""
    current_req_id = req_id or request_id_ctx.get() or "system"
    payload = APIErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details,
            request_id=current_req_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    """Register unified exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "AppException handled: [%s] %s (status=%d)",
            exc.code,
            exc.message,
            exc.status_code,
        )
        return create_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Simplify validation error details for consumer clarity
        formatted_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(x) for x in err.get("loc", []))
            formatted_errors.append({
                "location": loc,
                "message": err.get("msg"),
                "type": err.get("type"),
            })
        logger.warning("Validation error on %s %s: %s", request.method, request.url.path, formatted_errors)
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Request validation failed. Check 'details' for field-level errors.",
            details=formatted_errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            500: "INTERNAL_SERVER_ERROR",
            501: "NOT_IMPLEMENTED",
            503: "SERVICE_UNAVAILABLE",
        }
        error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
        logger.warning("HTTP %d on %s: %s", exc.status_code, request.url.path, exc.detail)
        return create_error_response(
            status_code=exc.status_code,
            code=error_code,
            message=str(exc.detail),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.error("Database error occurred: %s\n%s", str(exc), traceback.format_exc())
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DATABASE_ERROR",
            message="An unexpected database error occurred. Please try again later.",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.critical(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            str(exc),
            traceback.format_exc(),
        )
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
        )
