<!--
  Sync Impact Report
  ==================
  Version change: N/A → 1.0.0 (initial ratification)
  Modified principles: N/A (initial)
  Added sections:
    - Core Principles (3 principles)
    - Development Workflow
    - Technical Constraints
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ no update needed
      (Constitution Check section is dynamically filled by /speckit.plan)
    - .specify/templates/spec-template.md — ✅ no update needed
      (template is generic; principles enforced at plan/task level)
    - .specify/templates/tasks-template.md — ✅ no update needed
      (test-first ordering already present in template structure)
  Follow-up TODOs: none
-->

# Movie Buddy Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

TDD is mandatory for all production code in Movie Buddy.

- Tests MUST be written before implementation code.
- The Red-Green-Refactor cycle MUST be strictly followed:
  write a failing test, make it pass with minimal code, then refactor.
- Every public function and CLI command MUST have at least one
  corresponding test.
- Integration tests MUST cover kino.pub API interactions using
  recorded fixtures or mocks — live API calls in tests are forbidden.
- No pull request may be merged with failing tests.

**Rationale**: A CLI tool that integrates with an external API and
manages user data (ratings, watch history) requires high confidence
in correctness. TDD ensures regressions are caught early and that
the recommendation logic is verifiable.

### II. Simplicity / YAGNI

Every piece of code MUST justify its existence with a current,
concrete requirement.

- No speculative abstractions: do not build for hypothetical future
  needs.
- Prefer flat module structure over deep nesting.
- Prefer standard library solutions over third-party dependencies
  when the standard library is sufficient.
- Three similar lines of code are preferable to a premature
  abstraction.
- Configuration MUST use simple formats (environment variables,
  TOML/YAML files) — no custom configuration frameworks.
- External dependencies MUST be justified: each added dependency
  must solve a problem that cannot be reasonably solved with the
  standard library or existing dependencies.

**Rationale**: Movie Buddy is a focused CLI tool, not a framework.
Complexity slows development, increases maintenance burden, and
makes the codebase harder to contribute to. Keep it lean.

### III. Mindful User Experience

The CLI MUST be a pleasure to use — clear, beautiful, and
respectful of the user's time.

- All CLI output MUST use Rich (or equivalent) for formatted,
  colorful terminal rendering: tables, progress bars, panels.
- Error messages MUST be human-readable and actionable — never
  expose raw tracebacks or cryptic codes to the user.
- Long-running operations (API calls, recommendation computation)
  MUST show progress indicators.
- Command names and flags MUST follow CLI conventions: short,
  memorable, consistent (`movie-buddy watch`, `movie-buddy rate`,
  `movie-buddy recommend`).
- Output MUST degrade gracefully in non-interactive terminals
  (piped output, CI) — detect TTY and fall back to plain text.
- Help text for every command MUST be concise and include examples.

**Rationale**: A personal movie tracking tool lives or dies by how
enjoyable it is to use day-to-day. Beautiful output and thoughtful
interactions turn a utility into a tool users love.

## Development Workflow

- **Branching**: Feature branches off `main`; merge via pull request.
- **Commit discipline**: Each commit MUST be atomic — one logical
  change per commit with a descriptive message.
- **Code review**: All changes MUST be reviewed before merge
  (self-review acceptable for solo development).
- **Testing gate**: CI MUST run the full test suite; merges blocked
  on failure.
- **Formatting**: All Python code MUST be formatted with `ruff format`
  and pass `ruff check` with zero warnings before commit.
- **No secrets in version control**: All API keys, tokens, and
  credentials MUST be stored in `.env` (which is gitignored). Source
  files, documentation, fixtures, and config files MUST NOT contain
  secret values. Use `.env.example` with empty placeholders only.

## Technical Constraints

- **Language**: Python 3.14
- **CLI framework**: Typer or Click (TBD during planning)
- **Output formatting**: Rich
- **API integration**: kino.pub API via `httpx` (async-capable)
- **Data storage**: Local SQLite database for watch history and
  ratings
- **Testing**: pytest with pytest-httpx for API fixture recording
- **Linting/Formatting**: ruff
- **Full static typing**: MyPy with strict mode enabled

## Governance

This constitution is the supreme authority for Movie Buddy
development practices. All code contributions, reviews, and
architectural decisions MUST comply with the principles above.

- **Amendments**: Any change to this constitution MUST be documented
  with a version bump, rationale, and migration plan if the change
  affects existing code.
- **Versioning**: Constitution versions follow semantic versioning:
  - MAJOR: Principle removed or fundamentally redefined.
  - MINOR: New principle or section added, or material expansion.
  - PATCH: Wording clarifications, typo fixes.
- **Compliance review**: At the start of each feature, the
  implementation plan MUST include a Constitution Check gate
  verifying alignment with all principles.

**Version**: 1.1.0 | **Ratified**: 2026-02-13 | **Last Amended**: 2026-02-13
