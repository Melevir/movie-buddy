# Implementation Plan: Random Episode Opener

**Branch**: `001-random-episode` | **Date**: 2026-02-13 | **Spec**: `specs/001-random-episode/spec.md`
**Input**: Feature specification from `/specs/001-random-episode/spec.md`

## Summary

CLI tool that accepts a movie/series name, searches kino.pub via its
REST API, randomly selects an episode (for series), and opens the
corresponding kino.pub page in Chrome. Uses OAuth2 Device Flow for
authentication with encrypted local token storage. Prioritizes search
results based on user's watch history and bookmarks.

## Technical Context

**Language/Version**: Python 3.13+ (constitution says 3.14 but 3.13 is
what's installed; will target 3.13+ for compatibility)
**Primary Dependencies**: typer (CLI), httpx (HTTP, async-capable),
rich (terminal UX), cryptography (token encryption)
**Storage**: Encrypted binary file at `~/.config/movie_buddy/` for
OAuth tokens. No database for this feature.
**Testing**: pytest with pytest-httpx for API fixture mocking
**Target Platform**: macOS (primary), Linux (secondary)
**Project Type**: Single CLI application
**Performance Goals**: <5 seconds from command entry to browser open
(SC-001)
**Constraints**: Chrome required. kino.pub account required. No fuzzy
search available from API.
**Scale/Scope**: Single-user CLI tool, ~10 API calls per session max
**Linting/Formatting**: ruff (format + check)
**Type Checking**: mypy strict mode

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Test-First (NON-NEGOTIABLE)
- **PASS**: Sprint plan orders tests before implementation in every
  sprint. pytest + pytest-httpx for API mocking. No live API calls
  in tests.

### II. Simplicity / YAGNI
- **PASS**: Flat module structure. Only 4 external deps (typer, httpx,
  rich, cryptography) — each justified:
  - typer: CLI framework, vastly better than argparse for this use case
  - httpx: async HTTP, constitution mandates it
  - rich: constitution mandates it for CLI output
  - cryptography: user requested encrypted token storage
- No speculative abstractions. No database. No config framework.

### III. Mindful User Experience
- **PASS**: Rich output for all CLI responses. Progress indicators
  for API calls. Actionable error messages. TTY detection for
  graceful degradation.

### Development Workflow
- **PASS**: Feature branch `001-random-episode`. Atomic commits.
  ruff formatting. Full test suite gate.

### Green CI before passover for test
- **PASS**: CI configured to run pytest, ruff check, mypy and tests on all
  branches. Merges blocked on failure.

## Project Structure

### Documentation (this feature)

```text
specs/001-random-episode/
├── plan.md              # This file
├── api-research.md      # API research (already complete)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
movie_buddy/
├── __init__.py
├── __main__.py          # Entry point: python -m movie_buddy
├── cli.py               # Typer app, commands
├── api.py               # kino.pub API client (search, items, watching)
├── auth.py              # OAuth2 Device Flow + token storage
├── models.py            # Dataclasses: Content, Episode, Season, Token
├── browser.py           # Open Chrome with URL
└── config.py            # Paths, constants

tests/
├── conftest.py          # Shared fixtures (httpx mocks, sample data)
├── test_api.py          # API client tests
├── test_auth.py         # Auth flow tests
├── test_cli.py          # CLI integration tests
├── test_browser.py      # Browser opening tests
├── test_models.py       # Model tests
└── fixtures/            # Recorded API responses
    ├── search_friends.json
    ├── item_8894.json
    ├── watching_serials.json
    └── ...

pyproject.toml           # Project config (deps, ruff, mypy, pytest)
```

**Structure Decision**: Single project, flat module layout. No
`src/` directory — direct package at root (`movie_buddy/`). Tests
in sibling `tests/` directory. This is the simplest viable structure
for a CLI tool per YAGNI principle.

## Sprint Plan

Development is split into small sprints. User performs acceptance
testing after each sprint.

### Sprint 1: Project Skeleton + Auth (FR: auth prerequisite)

**Goal**: Working project scaffold with OAuth2 device flow. User can
authenticate and tokens are stored encrypted.

**Deliverables**:
- `pyproject.toml` with all dependencies and tool config
- `movie_buddy/config.py` — paths, constants
- `movie_buddy/models.py` — Token dataclass
- `movie_buddy/auth.py` — device flow, token storage (encrypted),
  token refresh
- `movie_buddy/cli.py` — `auth` command (triggers device flow)
- Tests for auth flow, token encryption/decryption
- ruff + mypy passing

**Acceptance test**: Run `python -m movie_buddy auth`, follow the
device flow, verify token is stored encrypted at
`~/.config/movie_buddy/`.

---

### Sprint 2: API Client + Search (FR-001, FR-002, FR-006, FR-008)

**Goal**: Working search command that finds content on kino.pub.

**Deliverables**:
- `movie_buddy/api.py` — KinoPubClient with search, get_item,
  get_watching methods
- `movie_buddy/models.py` — Content, Episode, Season dataclasses
- `movie_buddy/cli.py` — add `search` command (temporary, for
  testing)
- Tests with recorded API fixtures
- ruff + mypy passing

**Acceptance test**: Run `python -m movie_buddy search "Friends"`,
see formatted search results. Run with nonexistent name, see helpful
error.

---

### Sprint 3: Smart Match + Activity History (FR-005)

**Goal**: Search auto-selects best match using watch history and
bookmarks.

**Deliverables**:
- `movie_buddy/api.py` — add watching list + bookmarks fetching
- Match ranking logic: watching > bookmarks > first result
- Display auto-selected match or top-5 picker
- Tests for ranking logic with various scenarios
- ruff + mypy passing

**Acceptance test**: Search for a name that matches something in
your watching list — should auto-select. Search for an ambiguous
name not in watching list — should show top 5 picker.

---

### Sprint 4: Random Episode + Browser Open (FR-003, FR-004, FR-007)

**Goal**: Core feature complete — random episode selection and
Chrome opening.

**Deliverables**:
- `movie_buddy/browser.py` — open Chrome with URL
- Random episode selection logic (uniform across all seasons)
- `movie_buddy/cli.py` — main `watch` command wiring everything
  together
- Formatted output: show series name, S##E##, episode title
- Tests for random selection uniformity, URL construction, browser
  opening
- ruff + mypy passing

**Acceptance test**: Run `python -m movie_buddy watch "Friends"` —
Chrome opens with a random episode. Run again — different episode.
Run with a movie name — opens movie page directly.

---

### Sprint 5: Error Handling + Polish (FR-009, SC-005, SC-006, edge cases)

**Goal**: Production-quality error handling and UX polish.

**Deliverables**:
- Network error handling (timeout, unreachable, 401 refresh)
- Chrome-not-found detection
- No-internet detection
- Single-episode series handling
- TTY detection + plain text fallback
- Progress spinners during API calls
- Help text with examples for all commands
- Tests for all error scenarios
- ruff + mypy passing

**Acceptance test**: Disconnect internet — see friendly error. Test
with various edge cases from spec. Pipe output to file — no ANSI
codes.

## Complexity Tracking

No constitution violations. All choices align with principles.
