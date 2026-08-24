from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import sys
from typing import Any, Dict, Optional

# Context variable for tracing request IDs across async boundaries
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Logging filter that injects request_id from contextvars into the LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "system"
        return True


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured log aggregators with sensitive data redaction."""

    def format(self, record: logging.LogRecord) -> str:
        from app.services.redaction.redaction_service import redaction_service

        raw_msg = record.getMessage()
        redacted_msg = redaction_service.redact_text(raw_msg)

        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redacted_msg,
            "request_id": getattr(record, "request_id", "system"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = redaction_service.redact_text(self.formatException(record.exc_info))

        # Include custom extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = redaction_service.redact_structure(record.extra_data)

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with color coding, request ID, and redaction."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        from app.services.redaction.redaction_service import redaction_service

        color = self.COLORS.get(record.levelname, self.RESET)
        req_id = getattr(record, "request_id", "system")
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"{color}[{record.levelname:<8}]{self.RESET} {ts} [{req_id}] {record.name}:{record.lineno} -"
        raw_msg = record.getMessage()
        redacted_msg = redaction_service.redact_text(raw_msg)
        message = f"{prefix} {redacted_msg}"

        if record.exc_info:
            message += "\n" + redaction_service.redact_text(self.formatException(record.exc_info))

        return message


def setup_logging(log_level: str = "INFO", log_format: str = "console") -> logging.Logger:
    """Configure root logger with structured formatting and filter."""
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.addFilter(RequestIdFilter())

    if log_format.lower() == "json":
        stream_handler.setFormatter(JsonFormatter())
    else:
        stream_handler.setFormatter(ConsoleFormatter())

    root_logger.addHandler(stream_handler)

    # Silence overly verbose third-party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger = logging.getLogger("app")
    logger.info("Structured logging initialized (level=%s, format=%s)", log_level, log_format)
    return logger


def get_logger(name: str = "app") -> logging.Logger:
    """Get a named logger with proper filter configuration."""
    return logging.getLogger(name)
