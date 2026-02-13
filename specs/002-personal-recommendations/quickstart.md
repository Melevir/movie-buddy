# Quickstart: Personal Recommendations

**Date**: 2026-02-13

## Prerequisites

1. Feature 001 (random episode) is working — `movie-buddy auth`
   and `movie-buddy watch` function correctly.
2. Turso account created, database provisioned, credentials in
   `.env`:
   ```
   TURSO_DATABASE_URL=libsql://movie-buddy-<user>.turso.io
   TURSO_AUTH_TOKEN=<token>
   ```
3. OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=sk-...
   ```

## Scenario 1: First-time setup and rating

```bash
# 1. Build the recommendation catalog
movie-buddy catalog
# Expected: "Catalog updated: 450 new entries added. Total: 450"

# 2. Rate movies from your watching history
movie-buddy rate
# Expected: 10 movies presented one at a time.
#   "Матрица / The Matrix (1999) [movie]"
#   "Rate 1-10 (or Enter to skip): " → user types "9"
#   ... repeats for up to 10 movies
#   "Rated 8 movies. Total ratings: 8."

# 3. Rate more to reach the minimum (5)
# If fewer than 5 were rated, run again:
movie-buddy rate
```

## Scenario 2: Get recommendations

```bash
# Requires: at least 5 ratings + non-empty catalog
movie-buddy recommend "something light and funny for a rainy evening"
# Expected:
#   Spinner: "Generating recommendations..."
#   ┌───┬──────────────────────┬──────┬────────┬──────────────────┐
#   │ # │ Title                │ Year │ Type   │ Why              │
#   ├───┼──────────────────────┼──────┼────────┼──────────────────┤
#   │ 1 │ Друзья / Friends     │ 1994 │ serial │ Light comedy...  │
#   │ 2 │ Клиника / Scrubs     │ 2001 │ serial │ Similar humor... │
#   │ 3 │ Бруклин 9-9          │ 2013 │ serial │ Upbeat tone...   │
#   └───┴──────────────────────┴──────┴────────┴──────────────────┘
#   "Pick a number to open in Chrome (or Enter to skip): "
#   → user types "1" → opens in Chrome
```

## Scenario 3: View and manage ratings

```bash
# View all ratings
movie-buddy ratings
# Expected:
#   ┌──────────────────────────┬────────┬───────┬────────────┐
#   │ Title                    │ Type   │ Score │ Rated      │
#   ├──────────────────────────┼────────┼───────┼────────────┤
#   │ Матрица / The Matrix     │ movie  │   9   │ 2026-02-13 │
#   │ Друзья / Friends         │ serial │   8   │ 2026-02-13 │
#   │ ...                      │        │       │            │
#   └──────────────────────────┴────────┴───────┴────────────┘
#   "8 movies rated."

# Clear all ratings (with confirmation)
movie-buddy ratings --clear
# Expected: "Remove all ratings? (y/N): " → "y" → "All ratings cleared."
```

## Scenario 4: Grow catalog over time

```bash
# Run catalog periodically to discover new content
movie-buddy catalog
# Expected: "Catalog updated: 62 new entries added. Total: 512"

# Each run fetches fresh/hot/popular and deduplicates
movie-buddy catalog
# Expected: "Catalog updated: 15 new entries added. Total: 527"
```

## Scenario 5: Error cases

```bash
# No ratings yet → try to recommend
movie-buddy recommend "action movie"
# Expected: "You need at least 5 ratings. Run `movie-buddy rate` first."

# Empty catalog → try to recommend
movie-buddy recommend "comedy"
# Expected: "Catalog is empty. Run `movie-buddy catalog` first."

# No watching history on kino.pub
movie-buddy rate
# Expected: "No more movies to rate. Watch more content on kino.pub!"

# Missing OPENAI_API_KEY
movie-buddy recommend "thriller"
# Expected: "OPENAI_API_KEY not set. Add it to your .env file."

# Missing Turso credentials
movie-buddy rate
# Expected: "TURSO_DATABASE_URL not set. See quickstart guide for setup."
```

## Integration Points

| Component | Existing | New |
|-----------|----------|-----|
| Auth (OAuth2) | `auth.py` | Reused by `rate` (fetches watching history) |
| API client | `api.py` | Extended: new methods for watching history + catalog endpoints |
| Browser | `browser.py` | Reused by `recommend` (open selected recommendation) |
| CLI | `cli.py` | New commands: `rate`, `recommend`, `catalog`, `ratings` |
| Storage | — | New: `storage.py` (Turso client for ratings + catalog) |
| LLM | — | New: `recommender.py` (OpenAI integration for recommendations) |
| Config | `config.py` | Extended: Turso + OpenAI env vars |
| Models | `models.py` | Extended: CatalogEntry, Rating, Recommendation dataclasses |
