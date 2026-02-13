Á# Tasks: Random Episode Opener

**Input**: Design documents from `/specs/001-random-episode/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — constitution mandates TDD (Test-First, NON-NEGOTIABLE).

**Organization**: Tasks grouped by user story. Each sprint is independently testable by the user.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- All paths relative to repository root `/Users/melevir/projects/movie_buddy/`

---

## Phase 1: Setup (Project Skeleton)

**Purpose**: Project initialization, dependencies, tooling configuration.

- [x] T001 Create `pyproject.toml` with project metadata, dependencies (typer, httpx, rich, cryptography), dev dependencies (pytest, pytest-httpx, mypy, ruff), and tool config sections ([tool.ruff], [tool.mypy], [tool.pytest.ini_options])
- [x] T002 Create package structure: `movie_buddy/__init__.py`, `movie_buddy/__main__.py` (entry point calling `cli.app()`), empty `movie_buddy/cli.py`, `movie_buddy/config.py`
- [x] T003 [P] Create test structure: `tests/__init__.py`, `tests/conftest.py` (empty), `tests/fixtures/` directory
- [x] T004 [P] Create `movie_buddy/config.py` with dataclass-based config loading from env vars: `API_BASE_URL`, `OAUTH_URL`, `TOKEN_REFRESH_URL`, `CLIENT_ID`, `CLIENT_SECRET`, `CONFIG_DIR = ~/.config/movie_buddy`, `TOKEN_FILE = CONFIG_DIR/token.bin`, `KINOPUB_WEB_BASE`, `SUPPORTED_TYPES = ("movie", "serial", "tvshow")`
- [x] T005 Install project in dev mode (`pip install -e ".[dev]"`), verify `pytest`, `ruff check .`, `ruff format --check .`, and `mypy movie_buddy` all pass on empty project

**Checkpoint**: Project installable, all tooling passes on empty codebase.

---

## Phase 2: Foundational (Authentication)

**Purpose**: OAuth2 Device Flow + encrypted token storage. MUST complete before any API-dependent user story.

**Sprint 1 acceptance test**: Run `python -m movie_buddy auth`, complete device flow, verify encrypted token stored at `~/.config/movie_buddy/token.bin`.

### Tests (write FIRST, verify they FAIL)

- [x] T006 [P] Write tests for Token model in `tests/test_models.py`: construction, `is_expired` property, serialization to/from dict
- [x] T007 [P] Write tests for token encryption/decryption in `tests/test_auth.py`: encrypt+decrypt round-trip, decrypt with wrong key fails, load from nonexistent file returns None
- [x] T008 [P] Write tests for device flow in `tests/test_auth.py`: `start_device_flow` returns DeviceCode, `poll_for_token` handles pending/success/timeout (use pytest-httpx to mock API responses)
- [x] T009 [P] Write tests for token refresh in `tests/test_auth.py`: `refresh_token` returns new Token, `ensure_valid_token` refreshes expired token, raises AuthError when no token

### Implementation

- [x] T010 Create Token and DeviceCode dataclasses in `movie_buddy/models.py` with fields per data-model.md (Token: access_token, refresh_token, expires_at; DeviceCode: code, user_code, verification_uri, interval, expires_in)
- [x] T011 Create error types in `movie_buddy/models.py`: KinoPubError, AuthError, AuthTimeout, NetworkError, NotFoundError, RateLimitError (per api-client contract)
- [x] T012 Implement KinoPubAuth class in `movie_buddy/auth.py`: `_derive_key()` (machine-derived Fernet key from hostname+username hash), `save_token()` (serialize to JSON, encrypt with Fernet, write binary), `load_token()` (read binary, decrypt, deserialize, return Token or None)
- [x] T013 Implement device flow methods in `movie_buddy/auth.py`: `start_device_flow()` (POST to OAUTH_URL with grant_type=device_code), `poll_for_token()` (poll at interval, handle authorization_pending, raise AuthTimeout after expires_in)
- [x] T014 Implement `refresh_token()` and `ensure_valid_token()` in `movie_buddy/auth.py`: refresh via POST to TOKEN_REFRESH_URL, ensure_valid_token loads/checks expiry/refreshes
- [x] T015 Create minimal Typer app in `movie_buddy/cli.py` with `auth` command: calls start_device_flow, displays user_code and verification_uri with Rich panel, polls with Rich spinner, saves token on success, prints confirmation
- [x] T016 Verify all tests pass, `ruff check .`, `ruff format --check .`, `mypy movie_buddy` all green

**Checkpoint**: `python -m movie_buddy auth` works end-to-end. Token stored encrypted.

---

## Phase 3: User Story 1 — Open a random episode of a series (Priority: P1)

**Goal**: Type a series name, get a random episode opened in Chrome on kino.pub.

**Independent Test**: Run `python -m movie_buddy watch "Friends"` — Chrome opens a random episode. Run again — different episode.

**Sprint 2+4 combined**: API client + search + random episode + browser open.

### Tests (write FIRST, verify they FAIL)

- [x] T017 [P] [US1] Write tests for Content, Season, Episode models in `tests/test_models.py`: construction, URL generation (`build_watch_url` returns correct `/item/view/{id}/s{S}e{E}` pattern)
- [x] T018 [P] [US1] Write tests for KinoPubClient.search in `tests/test_api.py`: successful search returns list[Content], empty results returns [], filters by supported types. Use pytest-httpx with fixture `tests/fixtures/search_friends.json`
- [x] T019 [P] [US1] Write tests for KinoPubClient.get_item in `tests/test_api.py`: returns Content with populated seasons/episodes, uses nolinks=1. Use fixture `tests/fixtures/item_8894.json`
- [x] T020 [P] [US1] Write tests for random episode selection in `tests/test_cli.py`: selection covers all seasons (statistical test — run N times, verify episodes from multiple seasons appear), single-episode series returns that episode
- [x] T021 [P] [US1] Write tests for browser opening in `tests/test_browser.py`: `open_in_chrome` calls subprocess with correct args on macOS, raises error if Chrome not found (mock subprocess)

### Implementation

- [x] T022 [US1] Create Content, Season, Episode dataclasses in `movie_buddy/models.py` with fields per data-model.md. Add `build_watch_url()` method to Content that constructs the kino.pub web URL
- [x] T023 [US1] Create `tests/fixtures/search_friends.json` and `tests/fixtures/item_8894.json` with recorded API response structures (from api-research.md examples)
- [x] T024 [US1] Implement KinoPubClient class in `movie_buddy/api.py`: constructor takes Token, creates httpx.Client with Bearer auth header and base_url. Implement `search(query)` method: GET /v1/items/search?q={query}&type=serial,movie,tvshow, parse response into list[Content]
- [x] T025 [US1] Implement `get_item(item_id)` in `movie_buddy/api.py`: GET /v1/items/{id}?nolinks=1, parse response into Content with nested Season/Episode lists
- [x] T026 [US1] Implement `open_in_chrome(url)` in `movie_buddy/browser.py`: use subprocess to run `open -a "Google Chrome" {url}` on macOS. Detect platform for Linux variant (`google-chrome` / `chromium`). Raise descriptive error if Chrome not found
- [x] T027 [US1] Implement `watch` command in `movie_buddy/cli.py`: ensure_valid_token → search → if 1 result use it → get_item → flatten episodes → random.choice → print Rich panel (title, S##E##, episode title) → open_in_chrome. For 0 results: print error. For multiple results: for now just use first result (disambiguation comes in US2)
- [x] T028 [US1] Verify all tests pass, `ruff check .`, `ruff format --check .`, `mypy movie_buddy` all green

**Checkpoint**: `python -m movie_buddy watch "Breaking Bad"` opens random episode in Chrome. Single-result searches work end-to-end.

---

## Phase 4: User Story 2 — Handle ambiguous or missing series names (Priority: P2)

**Goal**: When search returns multiple results, smart-match using activity history or show interactive picker.

**Independent Test**: Search for "Friends" (multiple results) — if one is in watching list, auto-selects it. Otherwise shows top 5 picker. Search for nonsense — shows helpful error.

**Sprint 3**: Smart match + activity history.

### Tests (write FIRST, verify they FAIL)

- [x] T029 [P] [US2] Write tests for KinoPubClient.get_watching_serials and get_watching_movies in `tests/test_api.py`: returns list[WatchingItem]. Use fixture `tests/fixtures/watching_serials.json`
- [x] T030 [P] [US2] Write tests for KinoPubClient.get_bookmark_folders and get_bookmark_items in `tests/test_api.py`: returns folders list and item IDs. Use fixture `tests/fixtures/bookmarks.json`
- [x] T031 [P] [US2] Write tests for match ranking logic in `tests/test_cli.py`: (a) single search result → auto-select, (b) one result in watching list → auto-select with message, (c) one result in bookmarks → auto-select, (d) no activity match → return top 5 for picker, (e) 0 results → error message

### Implementation

- [x] T032 [US2] Create WatchingItem and BookmarkFolder dataclasses in `movie_buddy/models.py` per data-model.md
- [x] T033 [US2] Create fixtures `tests/fixtures/watching_serials.json`, `tests/fixtures/watching_movies.json`, `tests/fixtures/bookmarks.json`, `tests/fixtures/bookmark_items.json` with recorded API structures
- [x] T034 [US2] Implement `get_watching_serials()`, `get_watching_movies()`, `get_bookmark_folders()`, `get_bookmark_items(folder_id)` in `movie_buddy/api.py`
- [x] T035 [US2] Implement match ranking function in `movie_buddy/matcher.py`: fetch watching + bookmarks, cross-reference search result IDs, return auto-selected Content or top-5 list
- [x] T036 [US2] Update `watch` command in `movie_buddy/cli.py`: integrate ranking logic. If auto-selected, print "Auto-selected: {title} (in your watching list)". If top-5, display Rich numbered table and prompt for selection (1-5). Show Rich progress spinner during API calls (FR-008)
- [x] T037 [US2] Verify all tests pass, `ruff check .`, `ruff format --check .`, `mypy movie_buddy` all green

**Checkpoint**: `python -m movie_buddy watch "Friends"` auto-selects from watching list or shows picker. `python -m movie_buddy watch "xyznonexistent"` shows helpful error.

---

## Phase 5: User Story 3 — Handle movies (Priority: P3)

**Goal**: Movie names open movie page directly (no episode selection).

**Independent Test**: Run `python -m movie_buddy watch "The Matrix"` — opens movie page. Search with name matching both movie and series — shows both in picker.

### Tests (write FIRST, verify they FAIL)

- [ ] T038 [P] [US3] Write tests for movie handling in `tests/test_cli.py`: (a) movie selected → opens `https://kino.pub/item/view/{id}` (no /s/e suffix), (b) mixed movie+series results → both appear in picker with type labels
- [ ] T039 [P] [US3] Write test for Content.build_watch_url for movie type in `tests/test_models.py`: returns URL without season/episode suffix

### Implementation

- [ ] T040 [US3] Update Content.build_watch_url in `movie_buddy/models.py` to handle movie type: return `https://kino.pub/item/view/{id}` without episode path. Ensure series/tvshow path still works
- [ ] T041 [US3] Update `watch` command in `movie_buddy/cli.py`: if selected content is movie, skip episode selection, build movie URL directly, print Rich panel with title+year, open in Chrome. Add type label (Movie/Series/TV Show) to picker display
- [ ] T042 [US3] Create fixture `tests/fixtures/item_113_movie.json` (Matrix movie response) for movie detail tests
- [ ] T043 [US3] Verify all tests pass, `ruff check .`, `ruff format --check .`, `mypy movie_buddy` all green

**Checkpoint**: Movies and series both work. Type labels shown in multi-result picker.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, UX polish, edge cases (Sprint 5).

**Acceptance test**: Disconnect internet — friendly error. Pipe output to file — no ANSI codes. All edge cases from spec handled.

### Tests (write FIRST, verify they FAIL)

- [ ] T044 [P] Write tests for network error handling in `tests/test_api.py`: httpx.ConnectError → NetworkError, httpx.TimeoutException → NetworkError with timeout message, HTTP 429 → retry then RateLimitError, HTTP 401 → triggers token refresh
- [ ] T045 [P] Write tests for Chrome-not-found in `tests/test_browser.py`: subprocess fails with FileNotFoundError → user-friendly error message mentioning Chrome
- [ ] T046 [P] Write tests for CLI error display in `tests/test_cli.py`: NetworkError → "Unable to reach kino.pub" message, AuthError → "Please run `movie-buddy auth`" message, single-episode series → opens that episode without error

### Implementation

- [ ] T047 Add network error handling to KinoPubClient in `movie_buddy/api.py`: wrap httpx calls with try/except, convert httpx.ConnectError/TimeoutException to NetworkError, handle 429 with 5s retry (max 2), handle 401 with automatic token refresh
- [ ] T048 Add Chrome-not-found handling in `movie_buddy/browser.py`: catch subprocess errors, produce actionable error message
- [ ] T049 Update `movie_buddy/cli.py` error handling: wrap main flow in try/except for KinoPubError subtypes, display Rich-formatted error panels with actionable messages (SC-005). Add TTY detection: if not sys.stdout.isatty(), use plain text output (no Rich markup)
- [ ] T050 Add Rich progress spinners to all API calls in `movie_buddy/cli.py`: "Searching kino.pub...", "Fetching episode list...", "Checking your watching list..." (FR-008)
- [ ] T051 Add help text with examples to all Typer commands in `movie_buddy/cli.py`: auth (example flow), watch (example with series name and movie name), per CLI contract
- [ ] T052 Verify all tests pass, `ruff check .`, `ruff format --check .`, `mypy movie_buddy` all green. Run manual edge case tests from spec

**Checkpoint**: Production-quality CLI. All edge cases handled. Clean output in both TTY and piped modes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Auth)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — core feature
- **Phase 4 (US2)**: Depends on Phase 3 — extends search with disambiguation
- **Phase 5 (US3)**: Depends on Phase 3 — extends watch with movie support
- **Phase 6 (Polish)**: Depends on Phases 3-5

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2). No other story dependencies.
- **US2 (P2)**: Depends on US1 (extends the `watch` command's multi-result path).
- **US3 (P3)**: Depends on US1 (extends Content model and `watch` command). Can be parallel with US2.

### Within Each Phase

1. Tests written FIRST, verified to FAIL (TDD)
2. Models before services
3. Services before CLI integration
4. All tests green + linting/typing pass before checkpoint

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel:
- Phase 2: T006-T009 (all test files are independent)
- Phase 3: T017-T021 (test files), T022-T023 (models + fixtures)
- Phase 4: T029-T031 (test files)
- Phase 5: T038-T039 (test files)
- Phase 6: T044-T046 (test files)

US2 and US3 can be developed in parallel after US1 is complete.

---

## Implementation Strategy

### Sprint-Based Delivery (User Acceptance After Each)

1. **Sprint 1** → Phase 1 + Phase 2 (Setup + Auth) → User tests: `movie-buddy auth`
2. **Sprint 2** → Phase 3 (US1: Core watch) → User tests: `movie-buddy watch "Friends"`
3. **Sprint 3** → Phase 4 (US2: Smart match) → User tests: disambiguation scenarios
4. **Sprint 4** → Phase 5 (US3: Movies) → User tests: `movie-buddy watch "The Matrix"`
5. **Sprint 5** → Phase 6 (Polish) → User tests: edge cases, error scenarios

### MVP = Sprint 1 + Sprint 2

After Sprint 2, the tool is functional for exact-match series searches. This is the minimum viable product.

---

## Summary

| Phase | Tasks | Tests | Sprint |
|-------|-------|-------|--------|
| Setup | T001-T005 | — | 1 |
| Auth (Foundational) | T006-T016 | T006-T009 | 1 |
| US1: Random Episode | T017-T028 | T017-T021 | 2 |
| US2: Smart Match | T029-T037 | T029-T031 | 3 |
| US3: Movies | T038-T043 | T038-T039 | 4 |
| Polish | T044-T052 | T044-T046 | 5 |
| **Total** | **52 tasks** | **17 test tasks** | **5 sprints** |
