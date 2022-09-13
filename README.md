# zerochat

A very simple, command-line chat server and client using zeromq.

## features

- clients subscibe to a _channel_; they only see messages on that channel
- non-blocking input on the terminal

## architecture

- clients push a message to the server
- the server then publishes that message
- clients subscribe to published messages, filtering on the channel

```
[client] ---(push a message)--->  [server]
                                    / | \
                                   /  |  \
                        (publish message to subscribers)
                                 /    |    \
                                /     |     \
                           [client]   |      \
                                      |     [client]
                                   [client]
```

## usage

Check out the code, then run one of the following:

- To run the server: `python zerochat/server.py`
- To run the client: `python zerochat/client.py -u my_username`

You can see more options with:

- `python zerochat/server.py -h`.
- `python zerochat/client.py -h`.

## about

this is just a fun, little weekend project that lets me play with
[zeromq](https://zeromq.org) (which is pretty awesome).

## license

MIT. See the [`LICENSE.txt` file](LICENSE.txt).
