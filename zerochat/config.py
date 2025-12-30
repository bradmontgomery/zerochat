"""
Shared constants and configuration for zerochat.
"""

from __future__ import annotations

import re

# Default network configuration
DEFAULT_HOST: str = "localhost"
DEFAULT_SERVER_HOST: str = "*"  # Bind to all interfaces
DEFAULT_PUBSUB_PORT: str = "5555"
DEFAULT_RECV_PORT: str = "5556"
DEFAULT_SEND_PORT: str = "5556"  # Client sends to server's recv port

# Default user settings
DEFAULT_CHANNEL: str = "GLOBAL"
DEFAULT_USERNAME: str = "Anon"

# Validation patterns
MAX_USERNAME_LENGTH: int = 32
MAX_CHANNEL_LENGTH: int = 32
USERNAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_-]+$")
CHANNEL_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_username(username: str) -> str:
    """
    Validate and sanitize a username.

    Args:
        username: The username to validate.

    Returns:
        The validated username.

    Raises:
        ValueError: If the username is invalid.
    """
    username = username.strip()

    if not username:
        raise ValueError("Username cannot be empty")

    if len(username) > MAX_USERNAME_LENGTH:
        raise ValueError(f"Username cannot exceed {MAX_USERNAME_LENGTH} characters")

    if not USERNAME_PATTERN.match(username):
        raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")

    return username


def validate_channel(channel: str) -> str:
    """
    Validate and sanitize a channel name.

    Args:
        channel: The channel name to validate.

    Returns:
        The validated channel name (uppercase).

    Raises:
        ValueError: If the channel name is invalid.
    """
    channel = channel.strip().upper()

    if not channel:
        raise ValueError("Channel name cannot be empty")

    if len(channel) > MAX_CHANNEL_LENGTH:
        raise ValueError(f"Channel name cannot exceed {MAX_CHANNEL_LENGTH} characters")

    if not CHANNEL_PATTERN.match(channel):
        raise ValueError("Channel name can only contain letters, numbers, underscores, and hyphens")

    return channel
