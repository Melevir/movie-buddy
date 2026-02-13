# Research: Random Episode Opener

**Date**: 2026-02-13
**Status**: Complete

## Decision Log

### 1. API Integration Approach

**Decision**: Use kino.pub official REST API at `api.srvkp.com/v1`.

**Rationale**: The API is well-documented, provides all needed
endpoints (search, item details with episodes, watch history), and
has been verified with live testing. Web scraping would be fragile
(Cloudflare protection, HTML changes) and legally questionable.

**Alternatives considered**:
- Web scraping: Rejected — Cloudflare blocks non-browser requests,
  HTML structure is fragile, requires maintaining session cookies.
- Third-party wrappers: Only found archived JS library
  (nurikk/kinopub_api, 2021). Not maintained, wrong language.

**Reference**: Full API documentation in `api-research.md`.

### 2. Authentication Method

**Decision**: OAuth2 Device Flow using public client credentials
from the Kodi addon (credentials in `.env`).

**Rationale**: This is the standard auth method for kino.pub
device clients. The credentials are public (hardcoded in the
open-source Kodi addon). Device flow is ideal for CLI tools — user
authorizes in browser, no need to paste tokens manually.

**Alternatives considered**:
- Extract Chrome session cookies: Rejected — Chrome encrypts cookies
  with Keychain, fragile across Chrome updates, requires Chrome to
  be running.
- Register custom client_id: Requires contacting support@kino.pub.
  The Kodi credentials work and are public. Can register later if
  needed.
- Username/password auth: Not supported by the API.

### 3. Token Storage

**Decision**: Encrypted binary file at `~/.config/movie_buddy/`.
Use `cryptography` library (Fernet symmetric encryption) with a
machine-derived key.

**Rationale**: User explicitly requested encrypted storage rather
than raw JSON. `~/.config/` follows XDG convention. Fernet provides
authenticated encryption (AES-128-CBC + HMAC). Machine-derived key
(from hostname + username hash) provides basic protection against
casual file copying while remaining transparent to the user.

**Alternatives considered**:
- Raw JSON file: Rejected by user.
- macOS Keychain (`keyring`): More secure but adds platform-specific
  dependency. User chose file-based approach.
- Environment variables: Poor UX for persistent tokens.

### 4. CLI Framework

**Decision**: Typer (with Rich integration).

**Rationale**: Constitution specifies "Typer or Click". Typer is
built on Click and provides type-hint-based command definition,
automatic help generation, and native Rich integration. Less
boilerplate than Click for the same functionality.

**Alternatives considered**:
- Click: Typer's underlying library. More verbose but more flexible.
  For this simple tool, Typer's convenience wins.
- argparse: Constitution requires Typer or Click. Also lacks Rich
  integration and produces more boilerplate.

### 5. HTTP Client

**Decision**: httpx (synchronous mode for now).

**Rationale**: Constitution mandates httpx. Supports both sync and
async. For a CLI tool making 2-4 sequential API calls, sync is
simpler. Can upgrade to async later if needed (YAGNI).

**Alternatives considered**:
- requests: Simpler but constitution specifies httpx.
- aiohttp: Async-only, more complex, no added benefit for sequential
  CLI calls.

### 6. Search Result Disambiguation

**Decision**: Cross-reference search results against user's watching
list and bookmarks. Auto-select if exactly one match is in activity
history. Otherwise show top 5 for interactive selection.

**Rationale**: The API has no fuzzy search. Common queries return
many results (e.g. "Friends" → 96 results). Activity-based ranking
gives the best UX — the user probably means the show they're
currently watching. The `in_watchlist`/`bookmarks` fields in search
results are unreliable, so we fetch `/watching/serials`,
`/watching/movies`, and `/bookmarks/{id}` separately and
cross-reference by item ID.

**Alternatives considered**:
- Always show picker: Poor UX for frequently-watched shows.
- Fuzzy string matching on titles: Unreliable, doesn't capture
  user intent.
- Client-side caching of activity: Premature optimization (YAGNI).

### 7. Supported Content Types

**Decision**: `movie`, `serial`, `tvshow` only.

**Rationale**: User decision. These cover the primary use cases.
Documentaries, concerts, 3D, 4K are niche and can be added later
if needed.

### 8. Browser Opening

**Decision**: Use `subprocess` to launch Chrome via `open -a
"Google Chrome"` on macOS (or `google-chrome` / `chromium` on
Linux).

**Rationale**: The `webbrowser` stdlib module doesn't guarantee
Chrome specifically. Direct subprocess call allows targeting Chrome
and providing clear error if not found. Constitution says Chrome
is the only supported browser.

**Alternatives considered**:
- `webbrowser.open()`: Opens default browser, not necessarily
  Chrome. Spec requires Chrome specifically.
- Selenium/playwright: Overkill — we just need to open a URL.

### 9. Random Episode Selection

**Decision**: Flatten all episodes from all seasons into a single
list, pick uniformly at random using `random.choice()`.

**Rationale**: SC-004 requires uniform distribution across all
episodes. Flattening ensures no bias toward seasons with more or
fewer episodes.

**Alternatives considered**:
- Random season then random episode: Biases toward seasons with
  fewer episodes. Rejected per SC-004.
- Weighted random: No weighting requirements in spec.
