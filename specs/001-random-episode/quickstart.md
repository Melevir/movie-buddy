# Quickstart: Random Episode Opener

## Prerequisites

- Python 3.13+
- Google Chrome installed
- Active kino.pub account

## Setup

```bash
# Clone and enter project
cd movie_buddy

# Install in development mode
pip install -e ".[dev]"
```

## First Run

```bash
# Authenticate with kino.pub
movie-buddy auth
# Follow the on-screen instructions:
# 1. Go to https://kino.pub/device
# 2. Enter the displayed code
# 3. Wait for confirmation

# Open a random episode of a series
movie-buddy watch "Friends"

# Open a movie
movie-buddy watch "The Matrix"
```

## Development

```bash
# Run tests
pytest

# Run linter
ruff check .

# Run formatter
ruff format .

# Run type checker
mypy movie_buddy

# Run all checks
pytest && ruff check . && mypy movie_buddy
```

## Project Layout

```
movie_buddy/       # Main package
  cli.py           # CLI commands (typer app)
  api.py           # kino.pub API client
  auth.py          # OAuth2 device flow + token storage
  models.py        # Data models
  browser.py       # Chrome URL opener
  config.py        # Constants and paths

tests/             # Test suite
  fixtures/        # Recorded API responses
```

## Configuration

Tokens are stored at `~/.config/movie_buddy/token.bin` (encrypted).
To re-authenticate: `movie-buddy auth --force`.
