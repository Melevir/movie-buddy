# Feature Specification: Personal Recommendations

**Feature Branch**: `002-personal-recommendations`
**Created**: 2026-02-13
**Status**: Draft
**Input**: User description: "Starting new feature with user's ratings for different movies; add a command that asks for ratings of 10 movies user most likely watched and saves them to storage; add command that gives 3 proposals to watch that takes description with natural language and uses ratings to give better and more personal recommendations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rate familiar movies (Priority: P1)

As a user, I want the tool to present me with 10 movies I have
most likely watched (based on my kino.pub watching history) and
let me rate each one on a 1-10 scale, so that the system can learn
my preferences.

**Why this priority**: Ratings are the foundation for
personalization. Without collected preferences, the recommendation
command has nothing to work with.

**Independent Test**: Run `movie-buddy rate`. Verify that 10
movies appear one by one (sourced from the user's kino.pub watching
history), the user can rate each 1-10 or skip, and all ratings are
persisted to local storage. Run the command again and verify that
previously rated movies are not shown again — 10 new candidates
are presented instead.

**Acceptance Scenarios**:

1. **Given** the user has watching history on kino.pub, **When**
   the user runs `movie-buddy rate`, **Then** 10 movies from
   their history are presented one at a time for rating.
2. **Given** the user is presented with a movie to rate, **When**
   they enter a number 1-10, **Then** the rating is saved and the
   next movie is shown.
3. **Given** the user is presented with a movie to rate, **When**
   they press Enter without a number (or type "s"), **Then** the
   movie is skipped and the next one is shown.
4. **Given** the user has previously rated some movies, **When**
   they run `movie-buddy rate` again, **Then** only unrated movies
   from their history are presented.
5. **Given** the user has rated all movies from their history,
   **When** they run `movie-buddy rate`, **Then** the system
   displays a message saying there are no more movies to rate.

---

### User Story 2 - Get personalized recommendations (Priority: P2)

As a user, I want to describe what I am in the mood for in natural
language and get 3 movie/series recommendations that match both my
description and my personal taste (based on my ratings), so that I
can quickly find something good to watch.

**Why this priority**: This is the primary value of the feature —
turning ratings into actionable recommendations. Depends on US1
for rating data.

**Independent Test**: Run `movie-buddy recommend "something light
and funny for a rainy evening"`. Verify that 3 recommendations
are displayed with titles, years, and brief explanations of why
each was recommended. Verify that recommendations differ from a
user with different ratings given the same description.

**Acceptance Scenarios**:

1. **Given** the user has rated at least 5 movies, **When** they
   run `movie-buddy recommend "dark thriller with plot twists"`,
   **Then** 3 recommendations are displayed, each with title, year,
   type, and a brief reason why it was recommended.
2. **Given** the user selects one of the 3 recommendations, **When**
   the selection is confirmed, **Then** the content opens in Chrome
   (same behavior as `movie-buddy watch`).
3. **Given** the user has fewer than 5 ratings, **When** they run
   `movie-buddy recommend`, **Then** a message suggests running
   `movie-buddy rate` first to improve recommendations.
4. **Given** the user provides a natural language description,
   **When** recommendations are generated, **Then** the
   recommendations reflect both the description and the user's
   taste profile from their ratings.

---

### User Story 3 - View and manage ratings (Priority: P3)

As a user, I want to see all my ratings and optionally update or
remove individual ratings, so that I can correct mistakes or
reflect changed opinions.

**Why this priority**: Nice-to-have management capability. Core
functionality (rate + recommend) works without this.

**Independent Test**: Run `movie-buddy ratings` to see all saved
ratings in a formatted table. Run `movie-buddy ratings --clear`
to remove all ratings.

**Acceptance Scenarios**:

1. **Given** the user has saved ratings, **When** they run
   `movie-buddy ratings`, **Then** a formatted table of all rated
   movies with their scores is displayed, sorted by rating
   (highest first).
2. **Given** the user wants to start over, **When** they run
   `movie-buddy ratings --clear`, **Then** all ratings are removed
   after a confirmation prompt.

---

### Edge Cases

- What happens when the user has no watching history on kino.pub?
  The system MUST display a message suggesting the user watch some
  content on kino.pub first before rating.
- What happens when the recommendation service is unavailable or
  slow? The system MUST show a clear error with a timeout and
  suggest trying again.
- What happens when the user enters a rating outside 1-10? The
  system MUST reject the input and re-prompt with valid range.
- What happens when the natural language description is empty? The
  system MUST prompt the user to provide a description of what they
  want to watch.
- What happens when there are not enough unrated movies for a full
  session of 10? The system MUST present however many are available
  (even if fewer than 10) and inform the user.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `rate` command that presents
  movies from the user's kino.pub watching history for rating.
- **FR-002**: The `rate` command MUST present 10 movies per session
  (or fewer if not enough unrated movies remain).
- **FR-003**: Movies presented for rating MUST be sourced from the
  user's kino.pub watching history (serials and movies). Series
  are rated as a whole (one rating per title, not per episode).
- **FR-004**: Each rating MUST be an integer from 1 to 10. Users
  MUST be able to skip a movie without rating it.
- **FR-005**: Ratings MUST be persisted to shared remote storage
  accessible across devices. The storage service MUST be free at
  the project's scale.
- **FR-006**: Previously rated movies MUST NOT be presented again
  in subsequent rating sessions.
- **FR-007**: System MUST provide a `recommend` command that accepts
  a natural language description as input.
- **FR-008**: The `recommend` command MUST return exactly 3
  recommendations.
- **FR-009**: Recommendations MUST be personalized based on the
  user's ratings and the provided natural language description.
  Recommendations MUST be limited to content available on kino.pub.
- **FR-010**: Each recommendation MUST include the title, year,
  content type, and a brief explanation of why it was recommended.
- **FR-011**: After seeing recommendations, the user MUST be able to
  select one to open in Chrome (reusing existing watch flow).
- **FR-012**: System MUST require a minimum of 5 ratings before
  generating recommendations and display a helpful message if
  fewer exist.
- **FR-013**: System MUST provide a `ratings` command to view all
  saved ratings in a formatted table.
- **FR-014**: The `ratings` command MUST support a `--clear` flag
  to remove all ratings after confirmation.
- **FR-015**: System MUST show visual progress feedback during API
  calls and recommendation generation.
- **FR-016**: The LLM API key MUST be provided by the user via
  environment variable in `.env`. No API keys or secrets MUST be
  committed to version control.
- **FR-017**: System MUST provide a `catalog` command that fetches
  titles from kino.pub (popular, trending, top-rated categories)
  and appends new entries to the shared remote catalog. Repeated
  runs grow the catalog incrementally without replacing existing
  entries.
- **FR-018**: The recommendation engine MUST use the pre-fetched
  catalog as the candidate pool, not the LLM's general knowledge.
- **FR-019**: All persistent data (ratings, catalog) MUST be stored
  in shared remote storage that is accessible across the user's
  devices. The specific service will be determined during planning
  (must be free at project scale).

### Key Entities

- **Rating**: A user's score for a specific movie or series. Key
  attributes: kino.pub content ID, title, content type, score
  (1-10), date rated.
- **CatalogEntry**: A movie or series from kino.pub stored as a
  recommendation candidate. Key attributes: kino.pub content ID,
  title, year, content type, genres.
- **Recommendation**: A suggested movie or series with reasoning.
  Key attributes: content ID, title, year, content type,
  explanation text.
- **UserProfile**: Aggregated view of user preferences derived from
  ratings. Used to personalize recommendations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can complete their first rating session
  (10 movies) in under 3 minutes.
- **SC-002**: Recommendations are returned within 15 seconds of
  the user submitting their description.
- **SC-003**: At least 2 out of 3 recommendations are relevant to
  the user's description (as judged by the user).
- **SC-004**: Users with different rating profiles receive different
  recommendations for the same description.
- **SC-005**: All error scenarios produce messages that tell the
  user what went wrong and what to do next.
- **SC-006**: Rating and catalog data persists across sessions and
  is accessible from any of the user's devices.

### Assumptions

- The user has an active kino.pub account with some watching
  history. The tool uses the existing OAuth2 authentication from
  the `001-random-episode` feature.
- Recommendation generation uses an LLM (large language model) API
  to combine the user's taste profile with their natural language
  description and kino.pub's catalog. The specific LLM provider
  will be determined during planning.
- The kino.pub API provides enough metadata (title, year, type,
  genre) to build a meaningful taste profile from ratings.
- Ratings and catalog data are stored in a shared remote storage
  service (free tier, determined during planning) to enable
  cross-device access.
- The recommendation quality depends on the quality and quantity of
  user ratings — more ratings lead to better recommendations.
- Movies selected for rating are chosen from watching history
  because these are movies the user has actually seen and can
  rate meaningfully.

## Clarifications

### Session 2026-02-13
- Q: Must recommendations be limited to content available on kino.pub, or can the LLM suggest anything? → A: Only recommend content available on kino.pub (verified against catalog).
- Q: How is the LLM API key provided? → A: User provides their own key via `.env` file (same pattern as kino.pub credentials). No secrets committed to version control. Add no-secrets rule to project constitution.
- Q: How should the recommendation candidate pool be sourced? → A: Pre-fetch catalog from kino.pub via a dedicated `catalog` command and store in shared remote storage. All persistent data (ratings, catalog) must be in shared remote storage accessible across devices. Free service at project scale (determined during planning).
- Q: How should the catalog be populated and kept up to date? → A: Incremental — fetch popular/trending/top-rated categories from kino.pub and append new entries to existing catalog. Repeated runs grow the catalog without replacing existing entries.
- Q: Should users rate series as a whole or individual episodes? → A: Rate series as a whole (one rating per title, not per episode).
