# zerochat

[![Tests](https://github.com/bradmontgomery/zerochat/actions/workflows/tests.yml/badge.svg)](https://github.com/bradmontgomery/zerochat/actions/workflows/tests.yml)
[![GitHub tag](https://img.shields.io/github/v/tag/bradmontgomery/zerochat?label=latest)](https://github.com/bradmontgomery/zerochat/tags)
[![License](https://img.shields.io/github/license/bradmontgomery/zerochat)](LICENSE.txt)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A simple, command-line chat server and client using ZeroMQ with async I/O.

## Features

- Channel-based messaging — clients subscribe to a channel and only see messages on that channel
- Async I/O using `asyncio` and `zmq.asyncio` for non-blocking operation
- Rich terminal output with colored messages
- Structured JSON logging to file
- Input validation for usernames and channel names

## Architecture

- Clients push messages to the server
- The server publishes messages to all subscribers
- Clients subscribe to published messages, filtering by channel

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

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone https://github.com/bradmontgomery/zerochat.git
cd zerochat

# Install dependencies
uv sync
```

## Usage

### Running the Server

```bash
uv run zerochat-server
```

Server options:
```
-H, --host HOST          Hostname/IP to bind (default: *)
-p, --pubsub_port PORT   Port for publishing messages (default: 5555)
-r, --recv_port PORT     Port for receiving messages (default: 5556)
-v, --verbose            Enable verbose output
--log-file PATH          Custom log file path (default: ~/.zerochat/logs/server.log)
--log-console            Also log to console (stderr)
```

### Running the Client

```bash
uv run zerochat-client -u your_username
```

Client options:
```
-u, --username NAME      Your chat username (default: Anon)
-c, --channel NAME       Channel to join (default: GLOBAL)
-H, --host HOST          Server hostname/IP (default: localhost)
-p, --pubsub_port PORT   Server's publish port (default: 5555)
-s, --send_port PORT     Server's receive port (default: 5556)
--log-file PATH          Custom log file path (default: ~/.zerochat/logs/client.log)
--log-console            Also log to console (stderr)
```

### Example

Terminal 1 — Start the server:
```bash
uv run zerochat-server -v
```

Terminal 2 — Connect as Alice:
```bash
uv run zerochat-client -u Alice -c general
```

Terminal 3 — Connect as Bob:
```bash
uv run zerochat-client -u Bob -c general
```

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Run linters
uv run black zerochat/ tests/
uv run isort zerochat/ tests/
uv run flake8 zerochat/ tests/
uv run mypy zerochat/

# Or use make
make install   # Install dependencies and pre-commit hooks
make test      # Run tests
make lint      # Check linting
make format    # Auto-format code
```

## About

This is a fun weekend project for exploring [ZeroMQ](https://zeromq.org) pub/sub patterns.

## License

MIT. See the [`LICENSE.txt`](LICENSE.txt) file.
