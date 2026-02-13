# movie_buddy Development Guidelines

## Active Technologies

- Python 3.13+, Typer (CLI), httpx (HTTP), Rich (terminal UX), cryptography (token encryption), python-dotenv (env config)
- New in 002: openai (LLM recommendations), libsql-client (Turso remote storage)
- Storage: Turso (cloud-hosted SQLite via libSQL) — ratings + catalog tables
- Testing: pytest + pytest-httpx
- Linting: ruff (format + check, strict ruleset), mypy (strict mode)

## Project Structure

```text
movie_buddy/           # Main package
  __init__.py
  __main__.py          # Entry: python -m movie_buddy
  cli.py               # Typer app, commands
  api.py               # kino.pub API client
  auth.py              # OAuth2 Device Flow + token storage
  models.py            # Dataclasses + error types
  browser.py           # Chrome URL opener
  config.py            # Dataclass-based config, loads from env vars

tests/
  conftest.py
  test_api.py
  test_auth.py
  test_cli.py
  test_browser.py
  test_models.py
  fixtures/            # Recorded API responses

.env                   # Local env vars (gitignored)
.env.example           # Template for env vars
Makefile               # Dev commands
```

## Commands

```bash
make install-dev   # install with dev dependencies
make test          # run tests
make lint          # ruff check
make format        # ruff format
make typecheck     # mypy strict
make check         # lint + typecheck + test
make clean         # remove caches
```

## Code Style

- ruff format, ruff check (strict ruleset — zero warnings), mypy strict
- TDD mandatory: write failing test first, then implement
- No live API calls in tests — use pytest-httpx fixtures
- No unnecessary docstrings — only keep functional ones (e.g. Typer help strings)
- Full type annotations on all public functions
- Config via dataclass + env vars, no hardcoded secrets in source
- **No secrets in version control**: All API keys, tokens, and credentials MUST live in `.env` (gitignored). Never commit secret values to source files, docs, fixtures, or config. Use `.env.example` with empty placeholders only.

## Constitution

See `.specify/memory/constitution.md` for binding principles:
1. Test-First (NON-NEGOTIABLE) — TDD, Red-Green-Refactor
2. Simplicity / YAGNI — no speculative abstractions
3. Mindful UX — Rich output, actionable errors, progress indicators

## Feature: 001-random-episode

CLI tool to search kino.pub, pick random episode, open in Chrome.
API details: `specs/001-random-episode/api-research.md`
Spec: `specs/001-random-episode/spec.md`
Plan: `specs/001-random-episode/plan.md`

## Feature: 002-personal-recommendations

User ratings + LLM-powered personalized recommendations.
New commands: `rate`, `recommend`, `catalog`, `ratings`.
Storage: Turso (cloud SQLite). LLM: OpenAI GPT-4o-mini.
Spec: `specs/002-personal-recommendations/spec.md`
Plan: `specs/002-personal-recommendations/plan.md`
Research: `specs/002-personal-recommendations/research.md`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
