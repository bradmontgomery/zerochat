"""
A dead-simple command-line chat client using ZeroMQ.

TODO:

* support on-demand channel names?

"""

from __future__ import annotations

import argparse
import asyncio

import zmq
import zmq.asyncio
from aioconsole import ainput
from rich.console import Console
from rich.text import Text

CHANNEL: str = "GLOBAL"  # The default channel for messages
HOST: str = "localhost"  # Server Hostname or address
PUBSUB_PORT: str = "5555"  # Server's Pub/Sub port
SEND_PORT: str = "5556"  # Server's Recv port


class ZeroClient:
    def __init__(
        self,
        *,
        username: str = "Anon",
        host: str = HOST,
        channel: str = CHANNEL,
        send_port: str | int = SEND_PORT,
        pubsub_port: str | int = PUBSUB_PORT,
    ) -> None:
        self.username: str = username
        self.host: str = host
        self.console: Console = Console()

        # Set the channel string; format is `[channel_name]`
        self.channel: str = f"[{channel.strip().upper()}]"

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

    async def read_and_send(self) -> None:
        """Read user input and send messages to the server."""
        while True:
            try:
                msg = await ainput("")
                if msg.strip():
                    formatted = self._format_message(msg.strip())
                    await self.send_socket.send(formatted.encode("utf8"))
            except EOFError:
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
    # Username Argument
    parser.add_argument("-u", "--username", default="Anon", type=str, help="Your chat username")
    # Channel Argument
    parser.add_argument(
        "-c",
        "--channel",
        default=CHANNEL,
        type=str,
        help="The channel to which you wish to connect.",
    )
    # Host argument
    parser.add_argument(
        "-H",
        "--host",
        default=HOST,
        type=str,
        help="The hostname or IP address of the zerochat server",
    )
    # Pubsub Port argument
    parser.add_argument(
        "-p",
        "--pubsub_port",
        default=PUBSUB_PORT,
        type=int,
        help="The port used to Subscribe to Published messages",
    )
    # Send Port argument
    parser.add_argument(
        "-s",
        "--send_port",
        default=SEND_PORT,
        type=int,
        help="The port from which messages are Sent",
    )

    params = parser.parse_args()
    client = ZeroClient(
        channel=params.channel,
        username=params.username,
        host=params.host,
        pubsub_port=params.pubsub_port,
        send_port=params.send_port,
    )

    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        Console().print("\n[bold red]Disconnected.[/bold red]")


if __name__ == "__main__":
    main()
