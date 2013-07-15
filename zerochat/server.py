"""

A dead-simple command-line chat server using ZeroMQ.

TODO:
* support names for users (wo we know who's saying what)?

"""
import argparse
from sys import stdout

import re
import time
import zmq


HOST = "*"  # hostname or address to listen on
PUBSUB_PORT = "5555"
RECV_PORT = "5556"


class ZeroServer(object):

    def __init__(self, *args, **kwargs):
        self.verbose = kwargs.get('verbose', False)
        self.host = kwargs.get('host', HOST)

        # Port on which the server receives messages
        self.recv_port = kwargs.get('recv_port', RECV_PORT)
        self.recv_connection_string = "tcp://{host}:{port}".format(
            host=self.host,
            port=self.recv_port
        )

        # Port on which server publishes messages
        self.pubsub_port = kwargs.get('pubsub_port', PUBSUB_PORT)
        self.pubsub_connection_string = "tcp://{host}:{port}".format(
            host=self.host,
            port=self.pubsub_port
        )

        # Set up the networking
        self._create_context()
        self._create_recv_socket()
        self._create_pubsub_socket()

    def _create_context(self):
        self.context = zmq.Context()

    def _create_recv_socket(self):
        # Receive Socket: To receive messages
        self.recv_socket = self.context.socket(zmq.PULL)
        self.recv_socket.bind(self.recv_connection_string)

    def _create_pubsub_socket(self):
        # Pub/Sub socket: To Publish Chat Messages
        self.pubsub_socket = self.context.socket(zmq.PUB)
        self.pubsub_socket.bind(self.pubsub_connection_string)

    def recv_message(self):
        """Receives messages from the socket, and determines if there's any
        content worth publishing."""
        msg = self.recv_socket.recv()
        return self.validate_message(msg)

    def validate_message(self, msg):
        """All received message strings have a "channel" prefix of the form:

            '[CHANNEL] Username: The users's message here'

        To determine if we've got an empty message, we've got to strip off
        the channel bit, and see if there's anything left

        """
        msg = msg.strip()
        stripped_message = re.sub('^\[.+\] .+:', '', msg).strip()
        if stripped_message and self.verbose:
            stdout.write("[{0}] RECV: '{1}'\n".format(time.ctime(), msg))

        # If there's anything left after stripping off the channel prefix, then
        # we have a non-empty message; forward it on.
        if stripped_message:
            return msg

    def publish_message(self, msg):
        self.pubsub_socket.send(msg)
        if self.verbose:
            stdout.write("[{0}] PUB: '{1}'\n".format(time.ctime(), msg))

    def run(self):
        stdout.write("\nZero Server running:\n")
        stdout.write(" - Listening on '{0}'\n".format(
            self.recv_connection_string))
        stdout.write(" - Publishing to '{0}'\n".format(
            self.pubsub_connection_string))

        while True:
            # Receive a message...
            message = self.recv_message()

            # Publish the message for subscribers
            if message:
                self.publish_message(message)

            if self.verbose:
                stdout.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a zerochat server')
    # Host argument
    parser.add_argument('-H', '--host',
        dest="host",
        default=HOST,
        type=str,
        help='The hostname or IP address on which to bind (default: *)'
    )
    # Pubsub Port argument
    parser.add_argument('-p', '--pubsub_port',
        dest='pubsub_port',
        default=PUBSUB_PORT,
        type=int,
        help='The port on which messages are Published'
    )
    # Receive Port argument
    parser.add_argument('-r', '--recv_port',
        dest='recv_port',
        default=RECV_PORT,
        type=int,
        help='The port on which messages are Received'
    )
    # Verbosity argument
    parser.add_argument('-v', '--verbose',
        dest='verbose',
        action='store_true',
        help='The port on which messages are Received'
    )

    params = parser.parse_args()
    z = ZeroServer(
        host=params.host,
        pubsub_port=params.pubsub_port,
        recv_port=params.recv_port,
        verbose=params.verbose
    )
    z.run()
