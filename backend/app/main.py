from contextlib import asynccontextmanager
import time
import traceback
import uuid
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.database import check_database_connection
from app.core.errors import create_error_response, register_error_handlers
from app.core.logging import get_logger, request_id_ctx, setup_logging
from app.api.router import api_v1_router
from app.api.v1.health import router as health_router

settings = get_settings()
logger = setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware for Request ID injection, structured access logging, error envelope guarantee, and latency tracking."""

    async def dispatch(self, request: Request, call_next):
        # Generate or capture correlation request ID
        req_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
        token = request_id_ctx.set(req_id)
        request.state.request_id = req_id

        start_time = time.perf_counter()
        try:
            response: Response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            # Inject correlation ID and latency into response headers
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Response-Time-Ms"] = str(duration_ms)

            # Skip logging health check pings if in production to reduce noise
            if request.url.path not in ["/health/live", "/health/ready"]:
                logger.info(
                    "%s %s -> %d (%.2f ms)",
                    request.method,
                    request.url.path,
                    response.status_code,
                    duration_ms,
                )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.critical(
                "%s %s -> Unhandled Exception after %.2f ms: %s\n%s",
                request.method,
                request.url.path,
                duration_ms,
                exc,
                traceback.format_exc(),
            )
            # Ensure unhandled exceptions return the unified error contract response
            err_res = create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal server error occurred.",
                req_id=req_id,
            )
            err_res.headers["X-Request-ID"] = req_id
            err_res.headers["X-Response-Time-Ms"] = str(duration_ms)
            return err_res
        finally:
            request_id_ctx.reset(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan lifecycle manager."""
    logger.info("Initializing %s v%s in [%s] mode...", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    settings.ensure_directories()

    # Verify DB connectivity on startup
    db_check = check_database_connection()
    if db_check["connected"]:
        logger.info("Database connectivity established: %s (%s)", db_check["dialect"], db_check.get("database_target"))
    else:
        logger.warning("Database connectivity check failed: %s", db_check.get("error"))

    logger.info("Application startup complete. Ready to receive requests.")
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


def create_app() -> FastAPI:
    """FastAPI Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Phase 1 Foundation - AI Job Application Agent API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Add Request Context & Logging middleware
    app.add_middleware(RequestContextMiddleware)

    # 3. Register global error handlers
    register_error_handlers(app)

    # 4. Mount routers
    # Health checks available at root level
    app.include_router(health_router)
    # API v1 prefix routes
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["System Root"])
    def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "phase": "Phase 1 - Core Foundation",
            "docs": "/docs",
            "health": "/health",
            "api_v1": settings.API_V1_STR,
        }

    return app


app = create_app()
