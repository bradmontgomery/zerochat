"""
A dead-simple command-line chat server using ZeroMQ.

TODO:

* support names for users (so we know who's saying what)?
* support for persisting messages?
* include server-side time of message before sending it on?
* support for creating / connecting to a specified channel?
* announce user join / leaving?

"""

from __future__ import annotations

import argparse
import re
import time
from sys import stdout
from typing import NoReturn

import zmq

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
        self.context: zmq.Context[zmq.Socket[bytes]] = zmq.Context()

    def _create_recv_socket(self) -> None:
        # Receive Socket: To receive messages
        self.recv_socket: zmq.Socket[bytes] = self.context.socket(zmq.PULL)
        self.recv_socket.bind(self.recv_connection_string)

    def _create_pubsub_socket(self) -> None:
        # Pub/Sub socket: To Publish Chat Messages
        self.pubsub_socket: zmq.Socket[bytes] = self.context.socket(zmq.PUB)
        self.pubsub_socket.bind(self.pubsub_connection_string)

    def recv_message(self) -> bytes | None:
        """Receives messages from the socket, and determines if there's any
        content worth publishing."""
        msg = self.recv_socket.recv()
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
            stdout.write("[{0}] RECV: '{1}'\n".format(time.ctime(), decoded_msg))

        # If there's anything left after stripping off the channel prefix, then
        # we have a non-empty message; forward it on.
        if stripped_message:
            return decoded_msg.encode("utf8")
        return None

    def publish_message(self, msg: bytes) -> None:
        self.pubsub_socket.send(msg)
        if self.verbose:
            t = time.ctime()
            decoded_msg = msg.decode("utf8")
            stdout.write(f"[{t}] PUB: '{decoded_msg}'\n")

    def run(self) -> NoReturn:
        stdout.write("\nZero Server running:\n")
        stdout.write(f" - Listening on '{self.recv_connection_string}'\n")
        stdout.write(f" - Publishing to '{self.pubsub_connection_string}'\n")

        while True:
            # Receive a message...
            message = self.recv_message()

            # Publish the message for subscribers
            if message:
                self.publish_message(message)

            if self.verbose:
                stdout.flush()


def main():
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
        help="The port on which messages are Received",
    )

    params = parser.parse_args()
    z = ZeroServer(
        host=params.host,
        pubsub_port=params.pubsub_port,
        recv_port=params.recv_port,
        verbose=params.verbose,
    )
    z.run()


if __name__ == "__main__":
    main()
