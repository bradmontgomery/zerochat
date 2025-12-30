"""Tests for zerochat client and server classes."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zerochat.client import ZeroClient
from zerochat.server import ZeroServer


class TestZeroClient:
    """Tests for the ZeroClient class."""

    @patch("zerochat.client.zmq.asyncio.Context")
    def test_init_with_defaults(self, mock_context: MagicMock) -> None:
        """Client should initialize with default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "client.log"
            client = ZeroClient(log_file=log_file)

            assert client.username == "Anon"
            assert client.host == "localhost"
            assert client.channel == "[GLOBAL]"
            assert client.channel_name == "GLOBAL"

    @patch("zerochat.client.zmq.asyncio.Context")
    def test_init_with_custom_values(self, mock_context: MagicMock) -> None:
        """Client should accept custom configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "client.log"
            client = ZeroClient(
                username="alice",
                host="example.com",
                channel="testing",
                send_port=1234,
                pubsub_port=5678,
                log_file=log_file,
            )

            assert client.username == "alice"
            assert client.host == "example.com"
            assert client.channel == "[TESTING]"
            assert client.channel_name == "TESTING"
            assert client.send_port == 1234
            assert client.pubsub_port == 5678

    @patch("zerochat.client.zmq.asyncio.Context")
    def test_invalid_username_raises(self, mock_context: MagicMock) -> None:
        """Client should reject invalid usernames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "client.log"
            with pytest.raises(ValueError, match="can only contain"):
                ZeroClient(username="invalid user", log_file=log_file)

    @patch("zerochat.client.zmq.asyncio.Context")
    def test_invalid_channel_raises(self, mock_context: MagicMock) -> None:
        """Client should reject invalid channel names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "client.log"
            with pytest.raises(ValueError, match="can only contain"):
                ZeroClient(channel="invalid channel", log_file=log_file)

    @patch("zerochat.client.zmq.asyncio.Context")
    def test_format_message(self, mock_context: MagicMock) -> None:
        """Message formatting should include channel and username."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "client.log"
            client = ZeroClient(username="alice", channel="general", log_file=log_file)

            formatted = client._format_message("Hello world")

            assert formatted == "[GENERAL] alice: Hello world"


class TestZeroServer:
    """Tests for the ZeroServer class."""

    @patch("zerochat.server.zmq.asyncio.Context")
    def test_init_with_defaults(self, mock_context: MagicMock) -> None:
        """Server should initialize with default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "server.log"
            server = ZeroServer(log_file=log_file)

            assert server.host == "*"
            assert server.recv_port == "5556"
            assert server.pubsub_port == "5555"
            assert server.verbose is False

    @patch("zerochat.server.zmq.asyncio.Context")
    def test_init_with_custom_values(self, mock_context: MagicMock) -> None:
        """Server should accept custom configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "server.log"
            server = ZeroServer(
                host="127.0.0.1",
                recv_port=1234,
                pubsub_port=5678,
                verbose=True,
                log_file=log_file,
            )

            assert server.host == "127.0.0.1"
            assert server.recv_port == 1234
            assert server.pubsub_port == 5678
            assert server.verbose is True

    @patch("zerochat.server.zmq.asyncio.Context")
    def test_parse_message(self, mock_context: MagicMock) -> None:
        """Message parsing should extract channel, username, and content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "server.log"
            server = ZeroServer(log_file=log_file)

            parsed = server._parse_message("[GLOBAL] alice: Hello world")

            assert parsed["channel"] == "GLOBAL"
            assert parsed["username"] == "alice"
            assert parsed["content"] == "Hello world"
            assert parsed["raw"] == "[GLOBAL] alice: Hello world"

    @patch("zerochat.server.zmq.asyncio.Context")
    def test_parse_message_invalid_format(self, mock_context: MagicMock) -> None:
        """Parsing invalid message format should return raw only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "server.log"
            server = ZeroServer(log_file=log_file)

            parsed = server._parse_message("invalid message format")

            assert parsed["raw"] == "invalid message format"
            assert "channel" not in parsed
            assert "username" not in parsed

    @patch("zerochat.server.zmq.asyncio.Context")
    def test_validate_message_with_content(self, mock_context: MagicMock) -> None:
        """Messages with content should be validated and returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "server.log"
            server = ZeroServer(log_file=log_file)

            msg = b"[GLOBAL] alice: Hello world"
            result = server.validate_message(msg)

            assert result == msg

    @patch("zerochat.server.zmq.asyncio.Context")
    def test_validate_message_empty_content(self, mock_context: MagicMock) -> None:
        """Messages with empty content should return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "server.log"
            server = ZeroServer(log_file=log_file)

            msg = b"[GLOBAL] alice:    "
            result = server.validate_message(msg)

            assert result is None
