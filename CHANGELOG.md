# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Async/await support using `asyncio` and `zmq.asyncio` for non-blocking I/O
- Rich console output with colored messages (channel in cyan, username in yellow)
- Structured JSON logging to file (`~/.zerochat/logs/`)
- Input validation for usernames and channel names
- Graceful shutdown handling (Ctrl+C)
- CLI arguments for log file location (`--log-file`) and console logging (`--log-console`)
- Shared configuration module (`zerochat/config.py`) with validation functions
- Unit tests for config, logging, client, and server modules
- Type hints throughout the codebase
- mypy pre-commit hook

### Changed
- Converted project to use `uv` for dependency management
- Migrated from `requirements.txt` to `pyproject.toml`
- Updated all dependencies to latest versions (Dec 2025)
- Replaced blocking stdin reader with async `aioconsole.ainput()`
- Server and client now use `zmq.asyncio` for async socket operations
- Pre-commit flake8 hook now uses GitHub URL instead of GitLab

### Removed
- `reader.py` module (replaced by aioconsole)
- `requirements.txt` and `requirements.in` files
- `.isort.cfg` (config moved to pyproject.toml)
- Old-style `(object)` class inheritance
- Unused `*args` parameters

### Fixed
- Import error in client.py (changed to relative import)
- Variable shadowing in server's `validate_message` method

## [0.2.0] - 2022-09-01

### Added
- Initial public release
- ZeroMQ-based pub/sub chat server
- Command-line chat client
- Channel-based message filtering
- Non-blocking stdin reader

[Unreleased]: https://github.com/username/zerochat/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/username/zerochat/releases/tag/v0.2.0
