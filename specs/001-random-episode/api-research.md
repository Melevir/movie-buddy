# kino.pub API Research

**Date**: 2026-02-13
**Status**: Verified (all endpoints tested with live API)

## API Overview

- **Base URL**: `https://api.srvkp.com/v1`
- **Auth endpoint**: `https://api.srvkp.com/oauth2/device`
- **Documentation**: https://kinoapi.com/api_video.html
- **Reference implementation**: [Kodi addon](https://github.com/quarckster/kodi.kino.pub)

## Authentication — OAuth2 Device Flow

### Client Credentials
Public credentials from the Kodi addon. Values stored in `.env` (not committed to repo).

### Flow

**Step 1 — Get device code:**
```
POST https://api.srvkp.com/oauth2/device
Body: grant_type=device_code&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>
```
Response:
```json
{
  "code": "qkaklxybuxuyn1pmm5bg7jus7m5ish7i",
  "user_code": "SND5T",
  "verification_uri": "https://kino.pub/device",
  "interval": 5,
  "expires_in": 300
}
```

**Step 2 — User visits `https://kino.pub/device` and enters `user_code`.**

**Step 3 — Poll for token:**
```
POST https://api.srvkp.com/oauth2/device
Body: grant_type=device_token&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>&code=<device_code>
```
While pending: HTTP 400 `{"error": "authorization_pending"}`. Poll at `interval` seconds.
On success (HTTP 200):
```json
{
  "access_token": "278fdmaexxbjrxbwwkne4re9css54q40",
  "refresh_token": "bke3jakxkweu4t2dt7n9z0smn55zpe8y",
  "expires_in": 86400
}
```

**Token refresh:**
```
POST https://api.srvkp.com/oauth2/token
Body: grant_type=refresh_token&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>&refresh_token=<refresh_token>
```
Returns new `access_token` + `refresh_token`. All old tokens invalidated.

### Token Lifetimes
- `access_token`: 24 hours (86400 seconds)
- `refresh_token`: 30 days

### Auth Header
All API requests require: `Authorization: Bearer <access_token>`

## API Endpoints

### GET /v1/types
Returns all content types.
```json
{
  "status": 200,
  "items": [
    {"id": "movie", "title": "Фильмы"},
    {"id": "serial", "title": "Сериалы"},
    {"id": "tvshow", "title": "ТВ шоу"},
    {"id": "4k", "title": "4K"},
    {"id": "3d", "title": "3D"},
    {"id": "concert", "title": "Концерты"},
    {"id": "documovie", "title": "Документальные фильмы"},
    {"id": "docuserial", "title": "Документальные сериалы"}
  ]
}
```

### GET /v1/items/search
Search for content by name.

**Parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `q` | Yes | Search query string |
| `type` | No | Filter by type: `movie`, `serial`, `tvshow`, etc. |
| `field` | No | Search field: `title`, `director`, `cast` |
| `perpage` | No | Results per page (default ~20) |
| `sectioned` | No | If `1`, groups results by section |

**Example:**
```
GET /v1/items/search?q=Breaking+Bad
```
```json
{
  "status": 200,
  "items": [
    {
      "id": 8739,
      "type": "serial",
      "title": "Во все тяжкие / Breaking Bad",
      "year": 2008,
      "cast": "...",
      "director": "...",
      "genres": [{"id": 9, "title": "Драма"}],
      "countries": [{"id": 1, "title": "США"}],
      "quality": 1080,
      "plot": "...",
      "imdb_rating": 9.5,
      "kinopoisk_rating": 8.8,
      "posters": {
        "small": "https://m.pushbr.com/poster/item/small/8739.jpg",
        "medium": "...", "big": "...", "wide": "..."
      },
      "finished": true
    }
  ],
  "pagination": {
    "total": 1,
    "current": 1,
    "perpage": 20,
    "total_items": 2
  }
}
```

**Important behavior:**
- No fuzzy matching — misspelled queries (e.g. "Frends" instead of "Friends") return **0 results**
- Search works on both Russian and original-language titles (titles are stored as "Russian / English")
- Empty query returns all content (~52k items)
- Results sorted by relevance/recency, NOT by exact match quality

### GET /v1/items/{id}
Get full item details including seasons and episodes.

**Parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `nolinks` | No | If `1`, excludes streaming URLs from response (smaller payload) |

**Series response structure (tested with Friends, id=8894):**
```json
{
  "status": 200,
  "item": {
    "id": 8894,
    "type": "serial",
    "title": "Друзья / Friends",
    "year": 1994,
    "seasons": [
      {
        "number": 1,
        "episodes": [
          {
            "id": 104311,
            "number": 1,
            "snumber": 1,
            "title": "Эпизод, где Моника берёт новую соседку",
            "thumbnail": "https://m.pushbr.com/thumb/...",
            "duration": 1380,
            "tracks": null,
            "ac3": 0,
            "audios": [
              {
                "id": 3533944,
                "codec": "aac",
                "lang": "rus",
                "type": {"id": 2, "title": "Многоголосый"},
                "author": {"id": 76, "title": "РТР"}
              }
            ],
            "subtitles": [],
            "files": [
              {
                "codec": "h264",
                "w": 1920, "h": 1080,
                "quality": "1080p",
                "quality_id": 4,
                "url": {
                  "http": "https://digital-cdn.net/pd/...",
                  "hls": "https://digital-cdn.net/hls/...",
                  "hls4": "https://digital-cdn.net/hls4/...",
                  "hls2": "https://digital-cdn.net/hls2/..."
                }
              }
            ],
            "watched": 0,
            "watching": {}
          }
        ]
      }
    ]
  }
}
```

Friends has 10 seasons, 234 total episodes.

**Movie response structure:**
Movies have `videos[]` instead of `seasons[]`. Each video has the same structure as an episode.
```json
{
  "item": {
    "id": 113,
    "type": "movie",
    "title": "Матрица / The Matrix",
    "year": 1999,
    "videos": [
      {
        "id": 334,
        "number": 1,
        "title": "",
        "files": [...]
      }
    ]
  }
}
```

### Other Useful Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /v1/genres?type=<type>` | List genres, optionally filtered by content type |
| `GET /v1/countries` | List countries |
| `GET /v1/items/similar?id=<id>` | Get similar content |
| `GET /v1/items/fresh?type=<type>` | Fresh content by type |
| `GET /v1/items/hot?type=<type>` | Hot/trending content by type |
| `GET /v1/items/popular?type=<type>` | Popular content by type |
| `GET /v1/items/trailer?id=<id>` | Get trailer for an item |

## Web URL Patterns (verified in Chrome)

| Content Type | URL Pattern | Example |
|-------------|-------------|---------|
| Series episode | `https://kino.pub/item/view/{item_id}/s{season}e{episode}` | `https://kino.pub/item/view/8894/s3e7` |
| Movie | `https://kino.pub/item/view/{item_id}` | `https://kino.pub/item/view/113` |

**Note:** Opening a series URL without `/s{N}e{N}` suffix auto-redirects to `/s1e1`.

## Error Handling
- **401**: Token expired — trigger refresh flow
- **429**: Rate limited — retry after 5s delay (Kodi addon retries up to 2 times)
- **400** during auth polling: `{"error": "authorization_pending"}` — expected, keep polling
- **Cloudflare**: Direct `curl` to API may be blocked by Cloudflare; requests with proper headers work. The OAuth endpoint (`/oauth2/device`) is not Cloudflare-protected.

## Rate Limiting
No documented rate limits. The Kodi addon handles HTTP 429 with a 5-second backoff and max 2 retries.

## Activity / Watch History Endpoints

### GET /v1/watching/serials
Returns series the user is currently watching with progress.

**Parameters:** `perpage` (optional)

**Response:**
```json
{
  "status": 200,
  "items": [
    {
      "id": 110440,
      "type": "serial",
      "title": "Друзья и соседи / Your Friends & Neighbors",
      "subtype": "",
      "posters": {"small": "...", "medium": "...", "big": "..."},
      "total": 9,
      "watched": 0,
      "new": 9
    }
  ]
}
```

### GET /v1/watching/movies
Same structure as watching/serials but for movies.

### GET /v1/bookmarks
Returns bookmark folders.
```json
{
  "status": 200,
  "items": [
    {
      "id": 2576791,
      "title": "Буду смотреть",
      "views": 101,
      "count": 11,
      "created": 1763871399,
      "updated": 1770799584
    }
  ]
}
```

### GET /v1/bookmarks/{folder_id}
Returns items in a bookmark folder.

**Parameters:** `perpage` (optional)

**Response:** standard items list with `id`, `type`, `title`.

### Search results watch indicators
Each item in search results includes:
- `in_watchlist` (bool) — whether in user's watchlist
- `subscribed` (bool) — whether subscribed to updates
- `bookmarks` (list or null) — bookmark folder references

**Note:** These fields appear unreliable in search results (showed `False`/`None` even for items confirmed in watching list). More reliable to cross-reference against `/watching/serials` and `/watching/movies` by item ID.

## Key Design Considerations for Our Tool
1. **Token storage**: Need persistent storage for `access_token` and `refresh_token` (file-based, e.g. `~/.config/movie_buddy/token.json`)
2. **First-run auth**: On first run (no stored token), initiate device flow, show user code, wait for authorization
3. **Token refresh**: On 401 or before expiry, use refresh token automatically
4. **Search limitations**: No fuzzy search — tool may need to present multiple results even for slightly different queries
5. **Payload optimization**: Use `?nolinks=1` when fetching item details since we only need season/episode structure, not streaming URLs
