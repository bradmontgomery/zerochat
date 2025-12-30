"""
Structured logging configuration for zerochat.

Provides JSON-formatted logging to file by default, with optional console output.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

# Default log file location
DEFAULT_LOG_DIR = Path.home() / ".zerochat" / "logs"
DEFAULT_SERVER_LOG = DEFAULT_LOG_DIR / "server.log"
DEFAULT_CLIENT_LOG = DEFAULT_LOG_DIR / "client.log"


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "channel"):
            log_entry["channel"] = record.channel
        if hasattr(record, "username"):
            log_entry["username"] = record.username
        if hasattr(record, "host"):
            log_entry["host"] = record.host
        if hasattr(record, "port"):
            log_entry["port"] = record.port
        if hasattr(record, "event"):
            log_entry["event"] = record.event

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(
    name: str,
    *,
    log_file: Path | None = None,
    console: bool = False,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up structured logging for a zerochat component.

    Args:
        name: Logger name (e.g., "zerochat.server", "zerochat.client")
        log_file: Path to log file. If None, uses default based on name.
        console: If True, also log to console (plain format).
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Determine log file path
    if log_file is None:
        if "server" in name:
            log_file = DEFAULT_SERVER_LOG
        else:
            log_file = DEFAULT_CLIENT_LOG

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(StructuredFormatter())
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # Optional console handler with plain formatting
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    return logger
