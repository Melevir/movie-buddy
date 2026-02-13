# movie-buddy

CLI tool that searches [kino.pub](https://kino.pub) for a movie or series and opens a random episode in Chrome.

## Setup

```bash
# clone and install
git clone <repo-url> && cd movie_buddy
make install-dev

# configure credentials
cp .env.example .env
# edit .env and fill in KINOPUB_CLIENT_ID and KINOPUB_CLIENT_SECRET
```

## Authentication

movie-buddy uses kino.pub's OAuth2 Device Flow. Run once to link your account:

```bash
movie-buddy auth
```

Follow the on-screen instructions — visit the URL and enter the code. The token is encrypted and stored at `~/.config/movie_buddy/token.bin`.

Use `--force` to re-authenticate.

## Usage

```bash
# open a random episode of a series
movie-buddy watch "Friends"

# open a movie page
movie-buddy watch "Inception"
```

## Configuration

All settings are loaded from environment variables (with sensible defaults). Copy `.env.example` to `.env` to customize:

| Variable | Required | Description |
|---|---|---|
| `KINOPUB_CLIENT_ID` | Yes | OAuth2 client ID |
| `KINOPUB_CLIENT_SECRET` | Yes | OAuth2 client secret |
| `KINOPUB_API_BASE_URL` | No | API base URL (default: `https://api.srvkp.com/v1`) |
| `KINOPUB_OAUTH_URL` | No | OAuth2 device endpoint |
| `KINOPUB_TOKEN_REFRESH_URL` | No | Token refresh endpoint |
| `KINOPUB_WEB_BASE` | No | Web URL base for opening content |

## Development

```bash
make install-dev   # install with dev dependencies
make test          # run tests
make lint          # ruff check
make format        # ruff format
make typecheck     # mypy strict
make check         # lint + typecheck + test (all at once)
make clean         # remove caches and build artifacts
```

Requires Python 3.13+.
