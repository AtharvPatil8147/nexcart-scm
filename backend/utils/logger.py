"""
NexCart — Structured JSON Logger
==================================
Provides a get_logger(name) function used by all modules.
Logs JSON to stdout in development, to file in production.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional


class JsonFormatter(logging.Formatter):
    """Formats log records as structured JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Merge any extra fields passed via the `extra` kwarg
        if hasattr(record, "extra_data") and record.extra_data:
            log_entry["extra"] = record.extra_data

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class ExtraAdapter(logging.LoggerAdapter):
    """Adapter that injects extra_data into log records."""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = kwargs.get("extra", {})
        kwargs["extra"] = {"extra_data": extra}
        return msg, kwargs


# ── Module-level cache to avoid creating duplicate loggers ────────
_loggers: dict[str, ExtraAdapter] = {}


def get_logger(name: str) -> ExtraAdapter:
    """
    Get or create a structured JSON logger for the given module name.

    Args:
        name: Logger name (typically __name__ or a descriptive string)

    Returns:
        ExtraAdapter wrapping a standard Logger
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    # Prevent duplicate handlers if get_logger is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        formatter = JsonFormatter()

        app_env = os.getenv("APP_ENV", "development")

        if app_env == "production":
            # In production, log to a file
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(
                os.path.join(log_dir, "nexcart.log"),
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        else:
            # In development, log to stdout
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.DEBUG)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

        # Prevent propagation to root logger to avoid duplicate output
        logger.propagate = False

    adapter = ExtraAdapter(logger, {})
    _loggers[name] = adapter
    return adapter


print("✓ logger.py complete")
