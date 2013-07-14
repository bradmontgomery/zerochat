"""

A dead-simple command-line chat server using ZeroMQ.

TODO:
* support names for users (wo we know who's saying what)?

"""
from sys import argv, stdout, stderr
import zmq


HOST = "*"  # hostname or address to listen on
PUBSUB_PORT = "5555"
RECV_PORT = "5556"


class ZeroServer(object):

    def __init__(self, *args, **kwargs):
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

    def run(self):
        stdout.write("\nZero Server running:\n")
        stdout.write(" - Listening on '{0}'\n".format(
            self.recv_connection_string))
        stdout.write(" - Publishing to '{0}'\n".format(
            self.pubsub_connection_string))

        while True:
            # Receive a message...
            message = self.recv_socket.recv()

            # Publish the message for subscribers
            self.pubsub_socket.send(message)


if __name__ == "__main__":

    num_args = len(argv)
    if num_args not in [4, 2, 1]:
        stderr.write("\nUSAGE: python chat_server <host> "
                     "[pubsub_port] [recv_port]\n")
        quit()

    if len(argv) == 4:
        HOST = argv[1]
        PUBSUB_PORT = argv[2]
        RECV_PORT = argv[3]
    elif len(argv) == 2:
        HOST = argv[1]

    z = ZeroServer(host=HOST, pubsub_port=PUBSUB_PORT, recv_port=RECV_PORT)
    z.run()
