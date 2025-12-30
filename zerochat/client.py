"""
A dead-simple command-line chat client using ZeroMQ.

TODO:

* support on-demand channel names?

"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import zmq
import zmq.asyncio
from aioconsole import ainput
from rich.console import Console
from rich.text import Text

from .config import (
    DEFAULT_CHANNEL,
    DEFAULT_HOST,
    DEFAULT_PUBSUB_PORT,
    DEFAULT_SEND_PORT,
    DEFAULT_USERNAME,
    validate_channel,
    validate_username,
)
from .logging import setup_logging


class ZeroClient:
    def __init__(
        self,
        *,
        username: str = DEFAULT_USERNAME,
        host: str = DEFAULT_HOST,
        channel: str = DEFAULT_CHANNEL,
        send_port: str | int = DEFAULT_SEND_PORT,
        pubsub_port: str | int = DEFAULT_PUBSUB_PORT,
        log_file: Path | None = None,
        log_to_console: bool = False,
    ) -> None:
        self.username: str = validate_username(username)
        self.host: str = host
        self.console: Console = Console()
        self.logger = setup_logging(
            "zerochat.client",
            log_file=log_file,
            console=log_to_console,
        )

        # Validate and set the channel string; format is `[channel_name]`
        self.channel_name: str = validate_channel(channel)
        self.channel: str = f"[{self.channel_name}]"

        self.send_port: str | int = send_port
        self.send_connection_string: str = f"tcp://{self.host}:{self.send_port}"

        self.pubsub_port: str | int = pubsub_port
        self.pubsub_connection_string: str = f"tcp://{self.host}:{self.pubsub_port}"

        self._create_context()
        self._create_send_socket()
        self._create_pubsub_socket()

    def _create_context(self) -> None:
        self.context: zmq.asyncio.Context = zmq.asyncio.Context()

    def _create_send_socket(self) -> None:
        self.send_socket: zmq.asyncio.Socket = self.context.socket(zmq.PUSH)
        self.send_socket.connect(self.send_connection_string)

    def _create_pubsub_socket(self) -> None:
        self.pubsub_socket: zmq.asyncio.Socket = self.context.socket(zmq.SUB)
        self.pubsub_socket.connect(self.pubsub_connection_string)

        # Subscribe to the given channel
        self.pubsub_socket.setsockopt(zmq.SUBSCRIBE, self.channel.encode("utf8"))

    def _format_message(self, msg: str) -> str:
        """Adds in the Channel information."""
        return f"{self.channel} {self.username}: {msg}"

    def _get_prompt(self) -> str:
        """Return a styled prompt string for user input."""
        return f"[bold green]{self.username}>[/bold green] "

    def _print_prompt(self) -> None:
        """Print the input prompt without a newline."""
        self.console.print(self._get_prompt(), end="")

    async def read_and_send(self) -> None:
        """Read user input and send messages to the server."""
        while True:
            try:
                self._print_prompt()
                msg = await ainput("")
                if msg.strip():
                    formatted = self._format_message(msg.strip())
                    await self.send_socket.send(formatted.encode("utf8"))
                    self.logger.debug(
                        "Message sent",
                        extra={
                            "event": "message_sent",
                            "channel": self.channel_name,
                            "username": self.username,
                        },
                    )
            except EOFError:
                self.logger.info("Input stream closed", extra={"event": "input_closed"})
                break

    async def receive(self) -> None:
        """Receive and display published messages."""
        while True:
            msg = await self.pubsub_socket.recv()
            if msg:
                self.print_message(msg.decode("utf8"))

    def print_message(self, msg: str) -> None:
        """Prints received messages using rich console."""
        # Parse the message format: [CHANNEL] Username: message
        # Color the channel and username differently
        text = Text()
        if msg.startswith("["):
            bracket_end = msg.find("]")
            if bracket_end != -1:
                channel_part = msg[: bracket_end + 1]
                rest = msg[bracket_end + 1 :].strip()
                text.append(channel_part, style="bold cyan")
                text.append(" ")

                if ":" in rest:
                    username_part, message_part = rest.split(":", 1)
                    text.append(username_part, style="bold yellow")
                    text.append(":")
                    text.append(message_part, style="white")
                else:
                    text.append(rest)
            else:
                text.append(msg)
        else:
            text.append(msg)

        self.console.print(text)

    async def run(self) -> None:
        """Run the client with concurrent input and message receiving."""
        self.logger.info(
            "Client connecting",
            extra={
                "event": "client_connect",
                "host": self.host,
                "channel": self.channel_name,
                "username": self.username,
            },
        )

        self.console.print(
            f"[bold green]Connected to {self.host}[/bold green] "
            f"[dim]channel={self.channel}[/dim]"
        )
        self.console.print("[dim]Type your message and press Enter to send.[/dim]\n")

        # Run input reading and message receiving concurrently
        await asyncio.gather(
            self.read_and_send(),
            self.receive(),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a zerochat client")
    parser.add_argument(
        "-u", "--username", default=DEFAULT_USERNAME, type=str, help="Your chat username"
    )
    parser.add_argument(
        "-c",
        "--channel",
        default=DEFAULT_CHANNEL,
        type=str,
        help="The channel to which you wish to connect.",
    )
    parser.add_argument(
        "-H",
        "--host",
        default=DEFAULT_HOST,
        type=str,
        help="The hostname or IP address of the zerochat server",
    )
    parser.add_argument(
        "-p",
        "--pubsub_port",
        default=DEFAULT_PUBSUB_PORT,
        type=int,
        help="The port used to Subscribe to Published messages",
    )
    parser.add_argument(
        "-s",
        "--send_port",
        default=DEFAULT_SEND_PORT,
        type=int,
        help="The port from which messages are Sent",
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        type=Path,
        default=None,
        help="Path to log file (default: ~/.zerochat/logs/client.log)",
    )
    parser.add_argument(
        "--log-console",
        dest="log_console",
        action="store_true",
        help="Also log to console (stderr)",
    )

    params = parser.parse_args()
    console = Console()

    # Validate inputs before creating client
    try:
        validated_username = validate_username(params.username)
        validated_channel = validate_channel(params.channel)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    client = ZeroClient(
        channel=validated_channel,
        username=validated_username,
        host=params.host,
        pubsub_port=params.pubsub_port,
        send_port=params.send_port,
        log_file=params.log_file,
        log_to_console=params.log_console,
    )

    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        client.logger.info(
            "Client disconnected by user",
            extra={
                "event": "client_disconnect",
                "username": validated_username,
                "channel": validated_channel,
            },
        )
        console.print("\n[bold red]Disconnected.[/bold red]")


if __name__ == "__main__":
    main()
