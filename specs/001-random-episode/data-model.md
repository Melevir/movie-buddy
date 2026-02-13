# Data Model: Random Episode Opener

**Date**: 2026-02-13

## Entities

### Token

Represents the OAuth2 token pair stored locally.

| Field | Type | Description |
|-------|------|-------------|
| access_token | str | Bearer token for API requests |
| refresh_token | str | Token for refreshing access_token |
| expires_at | float | Unix timestamp when access_token expires |

**Storage**: Encrypted binary file at `~/.config/movie_buddy/token.bin`.
Serialized as JSON, then encrypted with Fernet (AES-128-CBC + HMAC).

**State transitions**:
```
[No token] --device_flow--> [Active]
[Active] --expired--> [Needs refresh]
[Needs refresh] --refresh--> [Active]
[Needs refresh] --refresh_failed--> [No token]
```

### Content

Represents a movie, series, or TV show from kino.pub search results.

| Field | Type | Description |
|-------|------|-------------|
| id | int | kino.pub item identifier |
| title | str | Display title (e.g. "Друзья / Friends") |
| content_type | str | One of: "movie", "serial", "tvshow" |
| year | int | Release year |
| seasons | list[Season] | Seasons with episodes (series/tvshow only) |

**Identity**: Unique by `id`.

**Validation**:
- `content_type` must be in `{"movie", "serial", "tvshow"}`
- `seasons` must be non-empty for series/tvshow
- `id` must be positive integer

### Season

A season within a series.

| Field | Type | Description |
|-------|------|-------------|
| number | int | Season number (1-based) |
| episodes | list[Episode] | Episodes in this season |

**Validation**:
- `number` must be positive integer
- `episodes` must be non-empty

### Episode

A single episode within a season.

| Field | Type | Description |
|-------|------|-------------|
| id | int | kino.pub episode identifier |
| number | int | Episode number within season (1-based) |
| title | str | Episode title |
| season_number | int | Parent season number (denormalized for convenience) |

**Identity**: Unique by `id`. Also uniquely identified by
`(content_id, season_number, number)`.

**Web URL**: Constructed as
`https://kino.pub/item/view/{content_id}/s{season_number}e{number}`

### WatchingItem

An item from the user's watching list (used for disambiguation).

| Field | Type | Description |
|-------|------|-------------|
| id | int | kino.pub item identifier |
| title | str | Display title |
| content_type | str | Content type |
| total | int | Total episodes |
| watched | int | Episodes watched |

### BookmarkFolder

A bookmark folder (used for disambiguation).

| Field | Type | Description |
|-------|------|-------------|
| id | int | Folder identifier |
| title | str | Folder name |

## Relationships

```
Content 1--* Season 1--* Episode
WatchingItem -.-> Content (same id, used for matching)
BookmarkFolder 1--* Content (via /bookmarks/{id} endpoint)
```

## URL Construction Rules

| Content Type | URL Pattern |
|-------------|-------------|
| serial / tvshow | `https://kino.pub/item/view/{content.id}/s{episode.season_number}e{episode.number}` |
| movie | `https://kino.pub/item/view/{content.id}` |
