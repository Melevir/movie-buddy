# Tasks: Personal Recommendations

**Input**: Design documents from `/specs/002-personal-recommendations/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md, quickstart.md

**Tests**: TDD is mandatory per constitution (Principle I). All tests written first, verified to fail, then implementation.

**Organization**: Tasks grouped by user story. Each story is independently testable after its phase completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependencies, extend config, create data model types

- [ ] T001 Add `openai` and `libsql-client` to project dependencies in pyproject.toml
- [ ] T002 [P] Add Turso and OpenAI env vars to movie_buddy/config.py (TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, OPENAI_API_KEY — all optional with None defaults)
- [ ] T003 [P] Update .env.example with empty placeholders for TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, OPENAI_API_KEY
- [ ] T004 [P] Add CatalogEntry, Rating, and Recommendation dataclasses to movie_buddy/models.py per data-model.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Turso storage client — MUST be complete before any user story

**CRITICAL**: All user stories depend on the storage layer

- [ ] T005 Write failing tests for Turso storage client in tests/test_storage.py: test schema init creates tables, test insert_ratings and get_ratings CRUD, test insert_catalog_entries and get_catalog_entries CRUD, test deduplication on insert (mock libsql)
- [ ] T006 Implement Turso storage client in movie_buddy/storage.py: TursoStorage class with init_schema(), insert_ratings(), get_ratings(), get_all_ratings(), delete_all_ratings(), insert_catalog_entries(), get_catalog_entries(), get_catalog_count() methods per data-model.md schema
- [ ] T007 Write failing test for missing Turso config (TURSO_DATABASE_URL not set) raises actionable error in tests/test_storage.py
- [ ] T008 Add config validation to movie_buddy/storage.py: raise KinoPubError with message "TURSO_DATABASE_URL not set. See quickstart guide for setup." when env vars missing

**Checkpoint**: Storage layer ready — user story implementation can begin

---

## Phase 3: User Story 1 — Rate Familiar Movies (Priority: P1) MVP

**Goal**: Present up to 10 movies from kino.pub watching history for 1-10 rating, persist to Turso

**Independent Test**: Run `movie-buddy rate`. Verify movies appear one at a time from watching history, user can rate 1-10 or skip, ratings persist. Run again — previously rated movies excluded.

### Tests for User Story 1

- [ ] T009 [P] [US1] Write failing tests for `rate` command in tests/test_cli.py: test presents movies from watching history for rating, test rating 1-10 saves to storage, test skip (Enter/s) moves to next, test quit (q) ends session early, test previously rated excluded, test no unrated movies shows message, test no watching history shows message, test fewer than 10 unrated shows available count, test summary message after session
- [ ] T010 [P] [US1] Write failing test for `rate` command error handling in tests/test_cli.py: test missing Turso config shows actionable message, test network error shows friendly message

### Implementation for User Story 1

- [ ] T011 [US1] Implement `rate` command in movie_buddy/cli.py per contracts/cli-commands.md: validate auth, fetch watching history (reuse existing get_watching_serials + get_watching_movies), load existing ratings from Turso, filter unrated, present up to 10 with Rich panels, prompt 1-10/skip/quit, save each rating to Turso, show summary
- [ ] T012 [US1] Add error handling wrapper for `rate` command in movie_buddy/cli.py: catch AuthError, NetworkError, KinoPubError with Rich panels (same pattern as `watch` command)
- [ ] T013 [US1] Verify all T009-T010 tests pass; run `make check`

**Checkpoint**: `movie-buddy rate` works end-to-end. Users can rate movies from their watching history.

---

## Phase 4: User Story 4 — Catalog Command (Prerequisite for US2)

**Goal**: Fetch content from kino.pub category endpoints and grow the recommendation catalog in Turso

**Independent Test**: Run `movie-buddy catalog`. Verify content fetched from fresh/hot/popular endpoints, stored in Turso with deduplication. Run again — only new entries added.

### Tests for Catalog

- [ ] T014 [P] Write failing tests for catalog API methods in tests/test_api.py: test get_category_items fetches from /items/{category} with type and perpage params, test returns list of CatalogEntry dataclasses with correct fields (id, title, year, content_type, genres, countries, imdb_rating, kinopoisk_rating, plot)
- [ ] T015 [P] Write failing tests for `catalog` command in tests/test_cli.py: test fetches 9 endpoints (3 categories x 3 types), test deduplicates against existing catalog, test shows progress messages, test shows summary with new + total counts, test network error handling

### Implementation for Catalog

- [ ] T016 Implement get_category_items(category, content_type, per_page) method in movie_buddy/api.py: call /items/{category} with type and perpage params, parse response into CatalogEntry dataclasses
- [ ] T017 Implement `catalog` command in movie_buddy/cli.py per contracts/cli-commands.md: validate auth, iterate 3 categories x 3 types, fetch via get_category_items, show progress, deduplicate, insert into Turso, show summary
- [ ] T018 Add error handling wrapper for `catalog` command in movie_buddy/cli.py
- [ ] T019 Create fixture files for catalog API responses in tests/fixtures/ (items_fresh_movie.json, items_hot_serial.json etc.)
- [ ] T020 Verify all T014-T015 tests pass; run `make check`

**Checkpoint**: `movie-buddy catalog` works end-to-end. Catalog grows incrementally.

---

## Phase 5: User Story 2 — Get Personalized Recommendations (Priority: P2)

**Goal**: Accept natural language description, generate 3 LLM-powered recommendations from catalog + taste profile

**Independent Test**: Run `movie-buddy recommend "something funny"` with ≥5 ratings and non-empty catalog. Verify 3 recommendations displayed with title/year/type/explanation. Select one to open in Chrome.

### Tests for User Story 2

- [ ] T021 [P] [US2] Write failing tests for recommender module in tests/test_recommender.py: test build_taste_profile from ratings, test build_prompt includes taste profile + catalog + description, test parse_recommendations extracts 3 Recommendation objects from LLM JSON response, test LLM error raises actionable message, test missing OPENAI_API_KEY raises actionable message
- [ ] T022 [P] [US2] Write failing tests for `recommend` command in tests/test_cli.py: test shows 3 recommendations in Rich table, test fewer than 5 ratings shows "rate first" message, test empty catalog shows "catalog first" message, test selecting number opens in Chrome, test Enter skips, test spinner shown during generation

### Implementation for User Story 2

- [ ] T023 [US2] Implement recommender module in movie_buddy/recommender.py: MovieRecommender class with build_taste_profile(ratings), build_prompt(taste_profile, catalog, description), get_recommendations(ratings, catalog, description) methods using OpenAI GPT-4o-mini with structured JSON output per research.md
- [ ] T024 [US2] Implement `recommend` command in movie_buddy/cli.py per contracts/cli-commands.md: validate auth, check ≥5 ratings, check non-empty catalog, call recommender, show spinner, display Rich table with 3 results, prompt to open in Chrome
- [ ] T025 [US2] Add error handling wrapper for `recommend` command in movie_buddy/cli.py: catch LLM errors, missing API key, AuthError, NetworkError
- [ ] T026 [US2] Verify all T021-T022 tests pass; run `make check`

**Checkpoint**: `movie-buddy recommend <description>` works end-to-end. Recommendations are personalized.

---

## Phase 6: User Story 3 — View and Manage Ratings (Priority: P3)

**Goal**: View all ratings in formatted table, clear all ratings with confirmation

**Independent Test**: Run `movie-buddy ratings` to see table. Run `movie-buddy ratings --clear` to remove all after confirmation.

### Tests for User Story 3

- [ ] T027 [P] [US3] Write failing tests for `ratings` command in tests/test_cli.py: test displays Rich table sorted by score (highest first), test shows total count, test no ratings shows "no ratings yet" message, test --clear with "y" deletes all ratings, test --clear with "n" cancels, test --clear with no ratings shows message

### Implementation for User Story 3

- [ ] T028 [US3] Implement `ratings` command in movie_buddy/cli.py per contracts/cli-commands.md: load ratings from Turso, display Rich table sorted by score, show total count. Support --clear flag with confirmation prompt.
- [ ] T029 [US3] Add error handling wrapper for `ratings` command in movie_buddy/cli.py
- [ ] T030 [US3] Verify all T027 tests pass; run `make check`

**Checkpoint**: `movie-buddy ratings` and `movie-buddy ratings --clear` work end-to-end.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, env example, cleanup

- [ ] T031 [P] Run full quickstart.md scenarios mentally: verify all 5 scenarios covered by implementation
- [ ] T032 [P] Run `make check` (lint + typecheck + test) — all must pass with zero warnings
- [ ] T033 Verify .env.example has all required vars with empty placeholders (no secrets)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 Rate (Phase 3)**: Depends on Phase 2 (storage)
- **Catalog (Phase 4)**: Depends on Phase 2 (storage). Can run in parallel with US1
- **US2 Recommend (Phase 5)**: Depends on Phase 3 (ratings exist) AND Phase 4 (catalog exists)
- **US3 Ratings view (Phase 6)**: Depends on Phase 2 (storage). Can run in parallel with US1/Catalog
- **Polish (Phase 7)**: Depends on all phases complete

### User Story Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Storage Foundation)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Phase 3 (US1 Rate)  Phase 4 (Catalog)  Phase 6 (US3 Ratings)
    │                  │
    └────────┬─────────┘
             ▼
      Phase 5 (US2 Recommend)
             │
             ▼
      Phase 7 (Polish)
```

### Within Each Phase

- Tests MUST be written and FAIL before implementation (TDD — Constitution Principle I)
- Models/dataclasses before storage methods
- Storage before CLI commands
- Core implementation before error handling
- Phase complete before verification task

### Parallel Opportunities

**Phase 1**: T002, T003, T004 can all run in parallel (different files)
**Phase 3 + Phase 4 + Phase 6**: Can run in parallel after Phase 2 completes
**Within phases**: Test tasks marked [P] can run in parallel with each other

---

## Parallel Example: After Phase 2

```
# These three phases can start simultaneously:
Phase 3: T009-T013 (US1 Rate command)
Phase 4: T014-T020 (Catalog command)
Phase 6: T027-T030 (US3 Ratings view)

# Phase 5 starts only after Phase 3 AND Phase 4 complete:
Phase 5: T021-T026 (US2 Recommend command)
```

---

## Implementation Strategy

### MVP First (Rate + Catalog)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Storage foundation (T005-T008)
3. Complete Phase 3: Rate command (T009-T013) — **users can rate movies**
4. Complete Phase 4: Catalog command (T014-T020) — **catalog populated**
5. **STOP and VALIDATE**: Rate and Catalog work independently

### Full Feature

6. Complete Phase 5: Recommend command (T021-T026) — **personalized recommendations**
7. Complete Phase 6: Ratings view (T027-T030) — **view/manage ratings**
8. Complete Phase 7: Polish (T031-T033) — **all checks pass**

### Incremental Delivery

- After Phase 3: Users can rate movies (value without recommendations)
- After Phase 4: Catalog populated for future recommendations
- After Phase 5: Full recommendation flow works
- After Phase 6: Complete ratings management
- Each phase adds value without breaking previous phases

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Constitution mandates TDD: tests written FIRST, verified to FAIL, then implementation
- All new env vars are optional (None default) to avoid breaking existing `auth`/`watch` commands
- Existing `get_watching_serials()` and `get_watching_movies()` in api.py are reused for US1
- Existing `open_in_chrome()` in browser.py is reused for US2
- Commit after each task or logical group
