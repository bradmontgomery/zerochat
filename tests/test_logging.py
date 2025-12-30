"""Tests for zerochat.logging module."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

from zerochat.logging import StructuredFormatter, setup_logging


class TestStructuredFormatter:
    """Tests for the structured JSON log formatter."""

    def test_basic_format(self) -> None:
        """Basic log records should format as valid JSON."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_extra_fields_included(self) -> None:
        """Extra fields should be included in the JSON output."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.channel = "GLOBAL"
        record.username = "testuser"
        record.event = "test_event"

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["channel"] == "GLOBAL"
        assert parsed["username"] == "testuser"
        assert parsed["event"] == "test_event"

    def test_timestamp_is_iso_format(self) -> None:
        """Timestamp should be in ISO 8601 format."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        # ISO format should contain 'T' separator and end with timezone
        assert "T" in parsed["timestamp"]


class TestSetupLogging:
    """Tests for the logging setup function."""

    def test_creates_logger(self) -> None:
        """setup_logging should return a configured logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging("test.setup", log_file=log_file)

            assert logger.name == "test.setup"
            assert logger.level == logging.INFO

    def test_creates_log_directory(self) -> None:
        """setup_logging should create the log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "subdir" / "test.log"
            setup_logging("test.mkdir", log_file=log_file)

            assert log_file.parent.exists()

    def test_writes_to_file(self) -> None:
        """Logger should write JSON to the specified file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging("test.write", log_file=log_file)

            logger.info("Test log message")

            content = log_file.read_text()
            assert "Test log message" in content

            # Verify it's valid JSON
            parsed = json.loads(content.strip())
            assert parsed["message"] == "Test log message"

    def test_console_handler_added_when_requested(self) -> None:
        """Console handler should be added when console=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            # Clear any existing handlers first
            logger_name = "test.console_unique"
            existing = logging.getLogger(logger_name)
            existing.handlers.clear()

            logger = setup_logging(logger_name, log_file=log_file, console=True)

            # Should have file handler + console handler
            assert len(logger.handlers) == 2

    def test_no_duplicate_handlers(self) -> None:
        """Calling setup_logging twice should not add duplicate handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger_name = "test.nodupe"

            # Clear any existing handlers
            existing = logging.getLogger(logger_name)
            existing.handlers.clear()

            logger1 = setup_logging(logger_name, log_file=log_file)
            handler_count = len(logger1.handlers)

            logger2 = setup_logging(logger_name, log_file=log_file)

            assert logger1 is logger2
            assert len(logger2.handlers) == handler_count
