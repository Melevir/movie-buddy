# Feature Specification: Random Episode Opener

**Feature Branch**: `001-random-episode`
**Created**: 2026-02-13
**Status**: Draft
**Input**: User description: "CLI tool that takes movie/series name as input and opens Chrome tab with random episode of the show at kino.pub"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open a random episode of a series (Priority: P1)

As a user, I want to type a series name into the command line and
have a random episode of that series open in my browser on kino.pub,
so that I can quickly start watching something without deciding
which episode to pick.

**Why this priority**: This is the entire core value proposition of
the tool. Without this, the tool does nothing.

**Independent Test**: Run the command with a known series name that
exists on kino.pub. Verify that a browser tab opens pointing to a
valid kino.pub episode URL for that series, and that the episode is
selected randomly (running the command multiple times produces
different episodes).

**Acceptance Scenarios**:

1. **Given** a series exists on kino.pub with multiple episodes,
   **When** the user runs the command with that series name,
   **Then** a Chrome tab opens with a randomly selected episode of
   that series on kino.pub.
2. **Given** a series exists on kino.pub with multiple seasons,
   **When** the user runs the command, **Then** the random selection
   spans all seasons and episodes (not just the first season).
3. **Given** the user runs the command twice with the same series,
   **When** both commands complete, **Then** different episodes are
   opened (with reasonable probability for series with more than a
   few episodes).

---

### User Story 2 - Handle ambiguous or missing series names (Priority: P2)

As a user, I want clear feedback when my search does not match
exactly one series, so that I can correct my input and try again.

**Why this priority**: Users will frequently mistype names or use
partial titles. Good error handling makes the tool usable in
practice.

**Independent Test**: Run the command with a misspelled or partial
series name. Verify the system either finds the best match or
presents a short list of candidates for the user to choose from.

**Acceptance Scenarios**:

1. **Given** the user enters a name that matches multiple series on
   kino.pub, **When** the command runs, **Then** a numbered list of
   matching series is displayed and the user is prompted to select
   one.
2. **Given** the user enters a name that matches no series on
   kino.pub, **When** the command runs, **Then** a clear message
   says no results were found and suggests checking the spelling.
3. **Given** the user enters a partial name that has a single close
   match, **When** the command runs, **Then** the tool uses that
   match and proceeds to open a random episode.

---

### User Story 3 - Handle movies (non-series content) (Priority: P3)

As a user, I want to be able to enter a movie name and have it
open directly on kino.pub, so that the tool works for all content
types, not just series.

**Why this priority**: Movies are simpler (no episode selection
needed) but the tool should not fail when a movie name is entered
instead of a series.

**Independent Test**: Run the command with a known movie name.
Verify that the kino.pub page for that movie opens in Chrome.

**Acceptance Scenarios**:

1. **Given** the user enters a movie name (not a series), **When**
   the command runs, **Then** the kino.pub page for that movie opens
   in Chrome.
2. **Given** the user enters a name that matches both a movie and a
   series, **When** the command runs, **Then** both are listed and
   the user chooses which one to open.

---

### Edge Cases

- What happens when kino.pub is unreachable? The tool MUST display
  a clear error message indicating the service is unavailable.
- What happens when Chrome is not installed or not found? The tool
  MUST display an error telling the user that Chrome is required
  and was not found on their system.
- What happens when a series has only one episode? The tool MUST
  open that single episode without error.
- What happens when the user has no internet connection? The tool
  MUST detect this and show a human-readable offline error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a movie or series name as
  command-line input.
- **FR-002**: System MUST search kino.pub for content matching the
  provided name, filtered to supported types (`movie`, `serial`,
  `tvshow`).
- **FR-003**: When the matched content is a series, the system MUST
  randomly select one episode from all available seasons and
  episodes.
- **FR-004**: System MUST open the selected episode (or movie) page
  on kino.pub in a Chrome browser tab.
- **FR-005**: When multiple results match the input, the system MUST
  first check if any match is in the user's watching list or
  bookmarks and auto-select it. If no activity match, display the
  top 5 results and let the user choose interactively.
- **FR-006**: When no results match the input, the system MUST
  display a helpful error message.
- **FR-007**: System MUST display a visually formatted output with
  the series/movie name, selected season/episode number, and episode
  title before opening the browser.
- **FR-008**: System MUST show progress feedback while searching
  kino.pub.
- **FR-009**: System MUST handle network errors gracefully with
  actionable error messages.

### Key Entities

- **Content**: A movie or series on kino.pub. Key attributes: title,
  type (movie or series), kino.pub identifier, kino.pub URL.
- **Episode**: A single episode within a series. Key attributes:
  season number, episode number, title, kino.pub URL.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From command entry to browser tab opening, the entire
  flow completes in under 5 seconds for an exact title match.
- **SC-002**: Users can discover and use the tool with zero
  configuration beyond authentication (if needed).
- **SC-003**: 90% of common series names (in their original
  language or Russian) produce a correct match on the first try.
- **SC-004**: The random episode selection is uniformly distributed
  across all available episodes (no bias toward specific seasons).
- **SC-005**: All error scenarios produce messages that tell the
  user what went wrong and what to do next.
- **SC-006**: The CLI output is visually formatted and pleasant to
  read in a terminal.

### Assumptions

- The user has an active kino.pub account and access to the content
  they search for. The tool does not handle subscription or payment
  concerns.
- kino.pub provides a way to look up content by name and retrieve
  episode listings. The specific mechanism will be determined during
  planning.
- "Random" means uniformly random across all episodes of all seasons
  of the matched series.
- Chrome is the only supported browser. The tool requires Chrome to
  be installed and will not fall back to other browsers.

### Technical details

- **API base URL**: `https://api.srvkp.com/v1`
- **Authentication**: OAuth2 Device Flow. Public client credentials
  (credentials sourced from `.env`, originally from the Kodi addon). Device flow: POST `/oauth2/device` with
  `grant_type=device_code` to get a user code, user visits
  `https://kino.pub/device` to authorize, then poll with
  `grant_type=device_token` to obtain `access_token` (24h) and
  `refresh_token` (30 days). Refresh via POST `/oauth2/token` with
  `grant_type=refresh_token`.
- **Search endpoint**: `GET /v1/items/search?q=<query>` — supports
  optional `type` (e.g. `serial`, `movie`), `field` (`title`,
  `director`, `cast`), `perpage` params. No fuzzy matching —
  misspellings return 0 results.
- **Item details**: `GET /v1/items/<id>` — returns `seasons[]` with
  nested `episodes[]` for series; `videos[]` for movies. Use
  `?nolinks=1` to omit streaming URLs and reduce payload.
- **Episode structure**: each episode has `id`, `number` (episode),
  season accessed via parent `seasons[].number`, `title`.
- **Web URL pattern**: `https://kino.pub/item/view/{item_id}/s{season}e{episode}`
  for series episodes; `https://kino.pub/item/view/{item_id}` for movies.
- **Content types**: `movie`, `serial`, `tvshow`, `4k`, `3d`,
  `concert`, `documovie`, `docuserial`.
- **Token storage**: `~/.config/movie_buddy/` directory, binary
  encrypted file (not raw JSON). Tokens auto-refresh on expiry.

### Technical stack
- **Language**: Python 3.13+
- **CLI framework**: `click` or `typer`
- **HTTP client**: `requests` or `httpx`
- **CLI UX**: `rich` (for formatted terminal output and progress feedback)

## Clarifications

### Session 2026-02-13
- Q: How should the tool interact with kino.pub? → A: Use kino.pub official API (`api.srvkp.com/v1`) with OAuth2 Device Flow authentication. Construct browser URLs as `https://kino.pub/item/view/{id}/s{season}e{episode}`.
- Q: What programming language and tech stack? → A: Python 3.13+ with `click`/`typer` for CLI, `requests`/`httpx` for HTTP, `rich` for terminal UX.
- Q: Where to store OAuth tokens between runs? → A: `~/.config/movie_buddy/` with binary encrypted storage (not raw JSON).
- Q: How to handle multiple search results? → A: Auto-guess best match using activity history (watching list, bookmarks). If a search result is in the user's watching list or bookmarks, prioritize it. Otherwise show top 5 results for user to pick.
- Q: Which content types to support? → A: `movie`, `serial`, `tvshow` only.
