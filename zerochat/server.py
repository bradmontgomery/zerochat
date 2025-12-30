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
import time

import zmq
import zmq.asyncio
from rich.console import Console

HOST: str = "*"  # hostname or address to listen on
PUBSUB_PORT: str = "5555"
RECV_PORT: str = "5556"


class ZeroServer:
    def __init__(
        self,
        *,
        verbose: bool = False,
        host: str = HOST,
        recv_port: str | int = RECV_PORT,
        pubsub_port: str | int = PUBSUB_PORT,
    ) -> None:
        self.verbose: bool = verbose
        self.host: str = host
        self.console: Console = Console()

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
        stripped_message = re.sub(r"^\[.+\] .+:", "", decoded_msg).strip()
        if stripped_message and self.verbose:
            self.console.print(f"[dim][{time.ctime()}][/dim] [cyan]RECV:[/cyan] '{decoded_msg}'")

        # If there's anything left after stripping off the channel prefix, then
        # we have a non-empty message; forward it on.
        if stripped_message:
            return decoded_msg.encode("utf8")
        return None

    async def publish_message(self, msg: bytes) -> None:
        await self.pubsub_socket.send(msg)
        if self.verbose:
            t = time.ctime()
            decoded_msg = msg.decode("utf8")
            self.console.print(f"[dim][{t}][/dim] [green]PUB:[/green] '{decoded_msg}'")

    async def run(self) -> None:
        self.console.print("\n[bold green]Zero Server running:[/bold green]")
        self.console.print(f" - Listening on [cyan]'{self.recv_connection_string}'[/cyan]")
        self.console.print(f" - Publishing to [cyan]'{self.pubsub_connection_string}'[/cyan]\n")

        while True:
            # Receive a message...
            message = await self.recv_message()

            # Publish the message for subscribers
            if message:
                await self.publish_message(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a zerochat server")
    # Host argument
    parser.add_argument(
        "-H",
        "--host",
        dest="host",
        default=HOST,
        type=str,
        help="The hostname or IP address on which to bind (default: *)",
    )
    # Pubsub Port argument
    parser.add_argument(
        "-p",
        "--pubsub_port",
        dest="pubsub_port",
        default=PUBSUB_PORT,
        type=int,
        help="The port on which messages are Published",
    )
    # Receive Port argument
    parser.add_argument(
        "-r",
        "--recv_port",
        dest="recv_port",
        default=RECV_PORT,
        type=int,
        help="The port on which messages are Received",
    )
    # Verbosity argument
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable verbose output",
    )

    params = parser.parse_args()
    server = ZeroServer(
        host=params.host,
        pubsub_port=params.pubsub_port,
        recv_port=params.recv_port,
        verbose=params.verbose,
    )

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        Console().print("\n[bold red]Server stopped.[/bold red]")


if __name__ == "__main__":
    main()
