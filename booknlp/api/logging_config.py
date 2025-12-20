"""Structured logging configuration for BookNLP API."""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Optional

from booknlp.api.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def __init__(self, include_timestamp: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if self.include_timestamp:
            log_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""
    
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Build prefix
        prefix_parts = [f"{color}{record.levelname}{self.RESET}"]
        
        if hasattr(record, "request_id"):
            prefix_parts.append(f"[{record.request_id[:8]}]")
        
        prefix = " ".join(prefix_parts)
        message = record.getMessage()
        
        # Add extra context
        extra_parts = []
        if hasattr(record, "method") and hasattr(record, "path"):
            extra_parts.append(f"{record.method} {record.path}")
        if hasattr(record, "status_code"):
            extra_parts.append(f"status={record.status_code}")
        if hasattr(record, "duration_ms"):
            extra_parts.append(f"duration={record.duration_ms}ms")
        
        if extra_parts:
            message = f"{message} ({', '.join(extra_parts)})"
        
        return f"{prefix}: {message}"


def configure_logging() -> None:
    """Configure logging based on settings."""
    settings = get_settings()
    
    # Get log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Choose formatter based on format setting
    if settings.log_format == "json":
        formatter = JSONFormatter(include_timestamp=settings.log_include_timestamp)
    else:
        formatter = ConsoleFormatter()
    
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]
    
    # Configure specific loggers
    logging.getLogger("booknlp").setLevel(log_level)
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
