"""

A dead-simple command-line chat client using ZeroMQ.

TODO:
* support names for users (wo we know who's saying what)?
* don't block on input (e.g. don't use raw_input) so we can see the chat
  happening in the background

"""

from sys import argv, stderr, stdout
import zmq

HOST = "localhost"  # Server Hostname or address
PUBSUB_PORT = "5555"  # Server's Pub/Sub port
SEND_PORT = "5556"  # Server's Recv port


class ZeroClient(object):

    def __init__(self, *args, **kwargs):
        self.host = kwargs.get('host', HOST)

        # Set the channel string; format is `[channel_name]`
        channel = kwargs.get('channel', 'global').strip().upper()
        self.channel = "[{0}]".format(channel)

        self.send_port = kwargs.get('send_port', SEND_PORT)
        self.send_connection_string = "tcp://{host}:{port}".format(
            host=self.host,
            port=self.send_port
        )
        self.pubsub_port = kwargs.get('pubsub_port', PUBSUB_PORT)
        self.pubsub_connection_string = "tcp://{host}:{port}".format(
            host=self.host,
            port=self.pubsub_port
        )

        self._create_context()
        self._create_send_socket()
        self._create_pubsub_socket()

    def _create_context(self):
        self.context = zmq.Context()

    def _create_send_socket(self):
        self.send_socket = self.context.socket(zmq.PUSH)
        self.send_socket.connect(self.send_connection_string)

    def _create_pubsub_socket(self):
        self.pubsub_socket = self.context.socket(zmq.SUB)
        self.pubsub_socket.connect(self.pubsub_connection_string)

        # Subscribe to the given channel
        self.pubsub_socket.setsockopt(zmq.SUBSCRIBE, self.channel)

    def _format_message(self, msg):
        # add in the channel info
        return "{0} {1}".format(self.channel, msg)

    def _read_message(self):
        msg = raw_input("MESSAGE: ")  # this'll block :-/
        return self._format_message(msg)

    def run(self):

        while True:
            msg = self._read_message()
            msg = msg.strip()
            if msg:
                self.send_socket.send(msg)

            # Receive any published messages
            msg = self.pubsub_socket.recv()
            if msg:
                msg = "{0}\n{1}\n".format(msg, '-' * len(msg))
                stdout.write(msg)
            stdout.flush()


if __name__ == "__main__":

    channel = "global"
    num_args = len(argv)
    if num_args not in [1, 2, 3, 5]:
        stderr.write("\nUSAGE: python chat_client [channel]"
                     " [host] [pubsub_port] [send_port]\n")
        quit()

    if num_args == 5:
        channel, host, pubsub_port, send_port = argv[1:5]
        HOST = host
        PUBSUB_PORT = pubsub_port
        SEND_PORT = send_port
    elif num_args == 3:
        channel, host = argv[1:3]
        HOST = host
    elif num_args == 2:
        channel = argv[1]

    z = ZeroClient(
        channel=channel,
        host=HOST,
        pubsub_port=PUBSUB_PORT,
        send_port=SEND_PORT
    )
    z.run()
