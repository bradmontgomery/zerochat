"""
A dead-simple command-line chat client using ZeroMQ.

TODO:

* support on-demand channel names?
* support names for users (wo we know who's saying what)?
* don't block on input so we can see the chat happening in the background

"""

import argparse
from sys import stdout

import zmq

from .reader import NonblockingStdinReader

CHANNEL = "GLOBAL"  # The default channel for messages
HOST = "localhost"  # Server Hostname or address
PUBSUB_PORT = "5555"  # Server's Pub/Sub port
SEND_PORT = "5556"  # Server's Recv port


class ZeroClient(object):
    def __init__(self, *args, **kwargs):
        self.username = kwargs.get("username", "Anon")
        self.host = kwargs.get("host", HOST)

        # Set the channel string; format is `[channel_name]`
        channel = kwargs.get("channel", CHANNEL).strip().upper()
        self.channel = f"[{channel}]"

        self.send_port = kwargs.get("send_port", SEND_PORT)
        self.send_connection_string = f"tcp://{self.host}:{self.send_port}"

        self.pubsub_port = kwargs.get("pubsub_port", PUBSUB_PORT)
        self.pubsub_connection_string = f"tcp://{self.host}:{self.pubsub_port}"

        self._create_context()
        self._create_send_socket()
        self._create_pubsub_socket()

        # to do non-blocking reads from stdin
        self.reader = NonblockingStdinReader()

    def _create_context(self):
        self.context = zmq.Context()

    def _create_send_socket(self):
        self.send_socket = self.context.socket(zmq.PUSH)
        self.send_socket.connect(self.send_connection_string)

    def _create_pubsub_socket(self):
        self.pubsub_socket = self.context.socket(zmq.SUB)
        self.pubsub_socket.connect(self.pubsub_connection_string)

        # Subscribe to the given channel
        self.pubsub_socket.setsockopt(zmq.SUBSCRIBE, self.channel.encode("utf8"))

    def _format_message(self, msg):
        """Adds in the Channel information."""
        return f"{self.channel} {self.username}: {msg}"

    def read_input(self):
        """Reads user input from the Terminal."""
        self.reader.read()
        msg = self.reader.get_input()
        if msg:
            return msg

    def send(self, msg):
        """Send messages to the server."""
        if msg:
            msg = self._format_message(msg)
            self.send_socket.send(msg.encode("utf8"))

    def receive(self, timeout=100):
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

    def print_message(self, msg):
        """Prints received messages to stdout."""
        stdout.write(f"\n{msg}\n")
        stdout.flush()

    def run(self):
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
