"""Tests for zerochat.config module."""

from __future__ import annotations

import pytest

from zerochat.config import (
    DEFAULT_CHANNEL,
    DEFAULT_HOST,
    DEFAULT_PUBSUB_PORT,
    DEFAULT_RECV_PORT,
    DEFAULT_USERNAME,
    MAX_CHANNEL_LENGTH,
    MAX_USERNAME_LENGTH,
    validate_channel,
    validate_username,
)


class TestConstants:
    """Tests for configuration constants."""

    def test_default_values_exist(self) -> None:
        """Verify all default constants are defined."""
        assert DEFAULT_HOST == "localhost"
        assert DEFAULT_PUBSUB_PORT == "5555"
        assert DEFAULT_RECV_PORT == "5556"
        assert DEFAULT_CHANNEL == "GLOBAL"
        assert DEFAULT_USERNAME == "Anon"

    def test_max_lengths_are_reasonable(self) -> None:
        """Verify max lengths are set to reasonable values."""
        assert MAX_USERNAME_LENGTH > 0
        assert MAX_CHANNEL_LENGTH > 0
        assert MAX_USERNAME_LENGTH <= 64
        assert MAX_CHANNEL_LENGTH <= 64


class TestValidateUsername:
    """Tests for username validation."""

    def test_valid_username(self) -> None:
        """Valid usernames should pass validation."""
        assert validate_username("alice") == "alice"
        assert validate_username("Bob123") == "Bob123"
        assert validate_username("user_name") == "user_name"
        assert validate_username("user-name") == "user-name"

    def test_username_strips_whitespace(self) -> None:
        """Whitespace should be stripped from usernames."""
        assert validate_username("  alice  ") == "alice"
        assert validate_username("\talice\n") == "alice"

    def test_empty_username_raises(self) -> None:
        """Empty usernames should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_username("")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_username("   ")

    def test_username_too_long_raises(self) -> None:
        """Usernames exceeding max length should raise ValueError."""
        long_username = "a" * (MAX_USERNAME_LENGTH + 1)
        with pytest.raises(ValueError, match="cannot exceed"):
            validate_username(long_username)

    def test_username_max_length_allowed(self) -> None:
        """Username at exactly max length should be allowed."""
        max_username = "a" * MAX_USERNAME_LENGTH
        assert validate_username(max_username) == max_username

    def test_invalid_characters_raise(self) -> None:
        """Usernames with invalid characters should raise ValueError."""
        with pytest.raises(ValueError, match="can only contain"):
            validate_username("user name")  # space
        with pytest.raises(ValueError, match="can only contain"):
            validate_username("user@name")  # @
        with pytest.raises(ValueError, match="can only contain"):
            validate_username("user.name")  # dot
        with pytest.raises(ValueError, match="can only contain"):
            validate_username("user:name")  # colon


class TestValidateChannel:
    """Tests for channel name validation."""

    def test_valid_channel(self) -> None:
        """Valid channel names should pass validation."""
        assert validate_channel("general") == "GENERAL"
        assert validate_channel("GLOBAL") == "GLOBAL"
        assert validate_channel("chat_room") == "CHAT_ROOM"
        assert validate_channel("room-1") == "ROOM-1"

    def test_channel_converts_to_uppercase(self) -> None:
        """Channel names should be converted to uppercase."""
        assert validate_channel("general") == "GENERAL"
        assert validate_channel("MyChannel") == "MYCHANNEL"

    def test_channel_strips_whitespace(self) -> None:
        """Whitespace should be stripped from channel names."""
        assert validate_channel("  general  ") == "GENERAL"

    def test_empty_channel_raises(self) -> None:
        """Empty channel names should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_channel("")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_channel("   ")

    def test_channel_too_long_raises(self) -> None:
        """Channel names exceeding max length should raise ValueError."""
        long_channel = "a" * (MAX_CHANNEL_LENGTH + 1)
        with pytest.raises(ValueError, match="cannot exceed"):
            validate_channel(long_channel)

    def test_channel_max_length_allowed(self) -> None:
        """Channel at exactly max length should be allowed."""
        max_channel = "a" * MAX_CHANNEL_LENGTH
        assert validate_channel(max_channel) == max_channel.upper()

    def test_invalid_characters_raise(self) -> None:
        """Channel names with invalid characters should raise ValueError."""
        with pytest.raises(ValueError, match="can only contain"):
            validate_channel("my channel")  # space
        with pytest.raises(ValueError, match="can only contain"):
            validate_channel("my#channel")  # hash
        with pytest.raises(ValueError, match="can only contain"):
            validate_channel("[global]")  # brackets
