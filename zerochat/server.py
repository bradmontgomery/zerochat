"""
A dead-simple command-line chat server using ZeroMQ.

TODO:

* support for persisting messages?
* include server-side time of message before sending it on?
* support for creating / connecting to a specified channel?
* announce user join / leaving?

"""

from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path

import zmq
import zmq.asyncio
from rich.console import Console

from .config import DEFAULT_PUBSUB_PORT, DEFAULT_RECV_PORT, DEFAULT_SERVER_HOST
from .logging import setup_logging


class ZeroServer:
    def __init__(
        self,
        *,
        verbose: bool = False,
        host: str = DEFAULT_SERVER_HOST,
        recv_port: str | int = DEFAULT_RECV_PORT,
        pubsub_port: str | int = DEFAULT_PUBSUB_PORT,
        log_file: Path | None = None,
        log_to_console: bool = False,
    ) -> None:
        self.verbose: bool = verbose
        self.host: str = host
        self.console: Console = Console()
        self.logger = setup_logging(
            "zerochat.server",
            log_file=log_file,
            console=log_to_console,
        )

        # Port on which the server receives messages
        self.recv_port: str | int = recv_port
        self.recv_connection_string: str = f"tcp://{self.host}:{self.recv_port}"

        # Port on which server publishes messages
        self.pubsub_port: str | int = pubsub_port
        self.pubsub_connection_string: str = f"tcp://{self.host}:{self.pubsub_port}"

        # Set up the networking
        self._create_context()
        self._create_recv_socket()
        self._create_pubsub_socket()

    def _create_context(self) -> None:
        self.context: zmq.asyncio.Context = zmq.asyncio.Context()

    def _create_recv_socket(self) -> None:
        # Receive Socket: To receive messages
        self.recv_socket: zmq.asyncio.Socket = self.context.socket(zmq.PULL)
        self.recv_socket.bind(self.recv_connection_string)

    def _create_pubsub_socket(self) -> None:
        # Pub/Sub socket: To Publish Chat Messages
        self.pubsub_socket: zmq.asyncio.Socket = self.context.socket(zmq.PUB)
        self.pubsub_socket.bind(self.pubsub_connection_string)

    def _parse_message(self, msg: str) -> dict[str, str]:
        """Parse a message into its components."""
        result: dict[str, str] = {"raw": msg}
        match = re.match(r"^\[([^\]]+)\]\s+([^:]+):\s*(.*)$", msg)
        if match:
            result["channel"] = match.group(1)
            result["username"] = match.group(2)
            result["content"] = match.group(3)
        return result

    async def recv_message(self) -> bytes | None:
        """Receives messages from the socket, and determines if there's any
        content worth publishing."""
        msg = await self.recv_socket.recv()
        return self.validate_message(msg)

    def validate_message(self, msg: bytes) -> bytes | None:
        """All received message strings have a "channel" prefix of the form:

            '[CHANNEL] Username: The users's message here'

        To determine if we've got an empty message, we've got to strip off
        the channel bit, and see if there's anything left

        """
        decoded_msg = msg.decode("utf8").strip()
        parsed = self._parse_message(decoded_msg)
        content = parsed.get("content", "").strip()

        if content:
            self.logger.info(
                "Message received",
                extra={
                    "event": "message_received",
                    "channel": parsed.get("channel", ""),
                    "username": parsed.get("username", ""),
                },
            )
            if self.verbose:
                self.console.print(f"[dim]RECV:[/dim] [cyan]{decoded_msg}[/cyan]")
            return decoded_msg.encode("utf8")
        return None

    async def publish_message(self, msg: bytes) -> None:
        await self.pubsub_socket.send(msg)
        decoded_msg = msg.decode("utf8")
        parsed = self._parse_message(decoded_msg)

        self.logger.info(
            "Message published",
            extra={
                "event": "message_published",
                "channel": parsed.get("channel", ""),
                "username": parsed.get("username", ""),
            },
        )
        if self.verbose:
            self.console.print(f"[dim]PUB:[/dim] [green]{decoded_msg}[/green]")

    async def run(self) -> None:
        self.logger.info(
            "Server starting",
            extra={
                "event": "server_start",
                "host": self.host,
                "recv_port": str(self.recv_port),
                "pubsub_port": str(self.pubsub_port),
            },
        )

        self.console.print("\n[bold green]Zero Server running:[/bold green]")
        self.console.print(f" - Listening on [cyan]'{self.recv_connection_string}'[/cyan]")
        self.console.print(f" - Publishing to [cyan]'{self.pubsub_connection_string}'[/cyan]\n")

        try:
            while True:
                # Receive a message...
                message = await self.recv_message()

                # Publish the message for subscribers
                if message:
                    await self.publish_message(message)
        except Exception as e:
            self.logger.exception("Server error", extra={"event": "server_error"})
            raise e


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a zerochat server")
    parser.add_argument(
        "-H",
        "--host",
        dest="host",
        default=DEFAULT_SERVER_HOST,
        type=str,
        help="The hostname or IP address on which to bind (default: *)",
    )
    parser.add_argument(
        "-p",
        "--pubsub_port",
        dest="pubsub_port",
        default=DEFAULT_PUBSUB_PORT,
        type=int,
        help="The port on which messages are Published",
    )
    parser.add_argument(
        "-r",
        "--recv_port",
        dest="recv_port",
        default=DEFAULT_RECV_PORT,
        type=int,
        help="The port on which messages are Received",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        type=Path,
        default=None,
        help="Path to log file (default: ~/.zerochat/logs/server.log)",
    )
    parser.add_argument(
        "--log-console",
        dest="log_console",
        action="store_true",
        help="Also log to console (stderr)",
    )

    params = parser.parse_args()
    logger = setup_logging("zerochat.server", log_file=params.log_file, console=params.log_console)

    server = ZeroServer(
        host=params.host,
        pubsub_port=params.pubsub_port,
        recv_port=params.recv_port,
        verbose=params.verbose,
        log_file=params.log_file,
        log_to_console=params.log_console,
    )

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user", extra={"event": "server_stop"})
        Console().print("\n[bold red]Server stopped.[/bold red]")


if __name__ == "__main__":
    main()
