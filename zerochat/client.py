"""
A dead-simple command-line chat client using ZeroMQ.

TODO:

* support on-demand channel names?
* support names for users (wo we know who's saying what)?
* don't block on input so we can see the chat happening in the background

"""

from __future__ import annotations

import argparse
from sys import stdout
from typing import NoReturn

import zmq

from .reader import NonblockingStdinReader

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

        # Set the channel string; format is `[channel_name]`
        self.channel: str = f"[{channel.strip().upper()}]"

        self.send_port: str | int = send_port
        self.send_connection_string: str = f"tcp://{self.host}:{self.send_port}"

        self.pubsub_port: str | int = pubsub_port
        self.pubsub_connection_string: str = f"tcp://{self.host}:{self.pubsub_port}"

        self._create_context()
        self._create_send_socket()
        self._create_pubsub_socket()

        # to do non-blocking reads from stdin
        self.reader: NonblockingStdinReader = NonblockingStdinReader()

    def _create_context(self) -> None:
        self.context: zmq.Context[zmq.Socket[bytes]] = zmq.Context()

    def _create_send_socket(self) -> None:
        self.send_socket: zmq.Socket[bytes] = self.context.socket(zmq.PUSH)
        self.send_socket.connect(self.send_connection_string)

    def _create_pubsub_socket(self) -> None:
        self.pubsub_socket: zmq.Socket[bytes] = self.context.socket(zmq.SUB)
        self.pubsub_socket.connect(self.pubsub_connection_string)

        # Subscribe to the given channel
        self.pubsub_socket.setsockopt(zmq.SUBSCRIBE, self.channel.encode("utf8"))

    def _format_message(self, msg: str) -> str:
        """Adds in the Channel information."""
        return f"{self.channel} {self.username}: {msg}"

    def read_input(self) -> str | None:
        """Reads user input from the Terminal."""
        self.reader.read()
        msg = self.reader.get_input()
        if msg:
            return msg
        return None

    def send(self, msg: str | None) -> None:
        """Send messages to the server."""
        if msg:
            msg = self._format_message(msg)
            self.send_socket.send(msg.encode("utf8"))

    def receive(self, timeout: int = 100) -> None:
        """Receive/print any published messages.

        Uses polling to keep from blocking when there are no messages to
        receive. Default timeout is 100ms.

        """
        # Poll to see if there's anything to receive
        if self.pubsub_socket.poll(timeout=timeout) > 0:
            # We have a message, so receive it!
            msg = self.pubsub_socket.recv()
            if msg:
                self.print_message(msg.decode("utf8"))

    def print_message(self, msg: str) -> None:
        """Prints received messages to stdout."""
        stdout.write(f"\n{msg}\n")
        stdout.flush()

    def run(self) -> NoReturn:
        while True:
            msg = self.read_input()  # Read input message from user
            self.send(msg)  # Send messages to chat server
            self.receive()  # Receive any published messages


def main():
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
    z = ZeroClient(
        channel=params.channel,
        username=params.username,
        host=params.host,
        pubsub_port=params.pubsub_port,
        send_port=params.send_port,
    )
    z.run()


if __name__ == "__main__":
    main()
