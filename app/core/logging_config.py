"""
Structured Logging Configuration
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Features:
- Structured JSON output in production
- Correlation ID propagation across asynchronous call chains
- Sensitive credential masking
- Standard Python logging integration
"""

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict

from app.config.settings import get_settings
from app.utils.sanitizer import SENSITIVE_KEY_PATTERNS, REDACTED_PLACEHOLDER

# Global ContextVar for Request Correlation ID tracking
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="SYSTEM_STARTUP")


class SecuritySensitiveFilter(logging.Filter):
    """
    Log filter that intercepts log records and scrubs any sensitive tokens or passwords
    found in message text or record arguments.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # Redact common pattern: password=..., token=..., Authorization: Bearer ...
            record.msg = SENSITIVE_KEY_PATTERNS.sub(REDACTED_PLACEHOLDER, record.msg)

        if isinstance(record.args, dict):
            record.args = {
                k: (REDACTED_PLACEHOLDER if SENSITIVE_KEY_PATTERNS.search(str(k)) else v)
                for k, v in record.args.items()
            }
        return True


class JSONLogFormatter(logging.Formatter):
    """
    Formats log records as structured JSON suitable for SIEM, ELK, or CloudWatch ingestion.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Include exception details if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra attributes if provided in record.__dict__
        for key, value in record.__dict__.items():
            if key not in [
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName"
            ]:
                log_entry[key] = value

        return json.dumps(log_entry)


class DevConsoleFormatter(logging.Formatter):
    """Clean readable formatter for local development console."""
    def format(self, record: logging.LogRecord) -> str:
        cid = correlation_id_ctx.get()
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        exc_text = f"\n{self.formatException(record.exc_info)}" if record.exc_info else ""
        return f"[{ts}] [{record.levelname:<8}] [{cid}] {record.name}: {record.getMessage()}{exc_text}"


def setup_logging() -> None:
    """Initializes application logging handlers based on environment settings."""
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.is_production or settings.LOG_FORMAT == "json":
        console_handler.setFormatter(JSONLogFormatter())
    else:
        console_handler.setFormatter(DevConsoleFormatter())

    if settings.MASK_SENSITIVE_DATA:
        console_handler.addFilter(SecuritySensitiveFilter())

    root_logger.addHandler(console_handler)

    # Ensure log file directory exists if file logging is enabled
    if settings.AUDIT_LOG_FILE_PATH:
        os.makedirs(os.path.dirname(settings.AUDIT_LOG_FILE_PATH), exist_ok=True)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """Returns a module-specific logger."""
    return logging.getLogger(name)
