# Research: Personal Recommendations

**Date**: 2026-02-13
**Status**: Complete

## Decision Log

### 1. Remote Storage Service

**Decision**: Turso (cloud-hosted SQLite via libSQL).

**Rationale**: Best free tier for the project's scale (500M reads,
10M writes/month, 5GB storage). SQLite query model is ideal for
structured data (ratings, catalog entries). No auto-pause on
inactivity (unlike Supabase). True cross-device access. Simple
Python integration via `libsql-client`. User creates a free Turso
account (GitHub OAuth), gets database URL + auth token, stores in
`.env`.

**Alternatives considered**:
- Supabase: Auto-pauses after 7 days of inactivity — dealbreaker
  for a CLI tool used intermittently.
- Firebase Firestore: More complex auth setup (service account
  JSON), daily limits. Workable but more friction.
- Google Sheets: Not a database, slow for queries, rate limits.
- jsonbin.io: 10k total requests — far too limiting.
- Cloudflare D1: Requires worker deployment, can't call directly.
- GitHub Gist: Not a database, no query support.

**Setup for user**:
1. Sign up at turso.tech (free, GitHub OAuth)
2. `turso db create movie-buddy`
3. `turso db show movie-buddy --url` → `TURSO_DATABASE_URL`
4. `turso db tokens create movie-buddy` → `TURSO_AUTH_TOKEN`
5. Add both to `.env`

### 2. LLM Provider

**Decision**: OpenAI GPT-4o-mini via `openai` Python SDK.

**Rationale**: Best balance of cost ($1.82/month for ~100 calls),
quality, and structured output support. Native JSON schema
validation ensures reliable parsing. 2-8 second response times
(well within 15s target). Mature, well-documented Python SDK.
User provides their own `OPENAI_API_KEY` in `.env`.

**Cost estimate**: ~121k input tokens per request (taste profile +
catalog of ~2000 entries + system prompt), ~400 output tokens.
At GPT-4o-mini pricing: ~$0.018 per call, ~$1.82/month for 100
calls.

**Alternatives considered**:
- Anthropic Claude Haiku: $12.30/month — 6x more expensive for
  similar quality at this task.
- Google Gemini Flash: $1.22/month — slightly cheaper but less
  mature structured output.
- Groq Llama 3.1: $0.73/month — cheaper but lower quality for
  nuanced recommendations.
- Ollama (local): Free but requires GPU hardware, inconsistent
  quality with small models.

**Multi-provider support**: Not initially. Cost difference is
minimal ($0.60-1.00/month) and not worth the complexity. Can add
later if needed (YAGNI).

### 3. Catalog Building Strategy

**Decision**: Fetch from 3 kino.pub category endpoints (fresh,
hot, popular) across 3 content types per run. 9 API calls total.
Incremental growth with deduplication by item ID.

**Rationale**: Category endpoints provide diverse, curated content
without requiring full catalog dumps. Fresh keeps catalog current,
hot captures trending, popular provides stable baseline. 50 items
per endpoint per run = ~450 fetched, ~300-400 unique after dedup.
10 runs builds ~1000 items.

**Endpoints used**:
- `GET /v1/items/fresh?type={type}&perpage=50`
- `GET /v1/items/hot?type={type}&perpage=50`
- `GET /v1/items/popular?type={type}&perpage=50`

**Growth trajectory**:
| Run | Fetched | New | Total |
|-----|---------|-----|-------|
| 1   | 450     | 450 | 450   |
| 5   | 450     | ~60 | ~825  |
| 10  | 450     | ~30 | ~1050 |

**Metadata stored per entry**: id, title, year, content_type,
genres (list), countries (list), imdb_rating, kinopoisk_rating,
plot. Excludes seasons/episodes/streaming URLs (fetch on-demand).

**Alternatives considered**:
- LLM suggests from general knowledge + verify on kino.pub: More
  API calls, unreliable for Russian content catalog.
- Full catalog dump via empty search query: 52k items, 1300+ pages,
  excessive for this use case.
- Genre-based fetching: Good for coverage expansion after base
  catalog established, but not needed initially.

### 4. Recommendation Prompt Strategy

**Decision**: Send the LLM the full catalog (as structured list)
+ user taste profile (rated titles with scores) + natural language
description. LLM selects 3 items from the catalog and explains why.

**Rationale**: With a catalog of ~1000-5000 entries at ~100 tokens
per entry, total input fits within GPT-4o-mini's 128k context
window. Structured output (JSON schema) ensures reliable parsing.
The LLM's strength is understanding the natural language description
and matching it against genres, ratings, and plot descriptions.

**Prompt structure**:
1. System: "You are a movie recommender. Select exactly 3 items
   from the provided catalog..."
2. User taste profile: List of rated titles with scores
3. Catalog: JSON array of all catalog entries
4. User request: The natural language description

### 5. Storage Schema Design

**Decision**: Two tables in Turso — `ratings` and `catalog`.

**Rationale**: Clean separation of user-specific data (ratings) and
shared data (catalog). Both accessible via SQL queries. Simple
schema, no joins needed for most operations.

**Tables**:
- `catalog`: id (PK), title, year, content_type, genres (JSON),
  countries (JSON), imdb_rating, kinopoisk_rating, plot, created_at
- `ratings`: content_id (PK), title, content_type, score, rated_at

### 6. New Dependencies

**Decision**: Add `openai` and `libsql-client` to project
dependencies.

**Rationale**:
- `openai`: Official OpenAI SDK. Needed for LLM-powered
  recommendations. Supports structured output with Pydantic schemas.
  No reasonable standard library alternative.
- `libsql-client`: Official Turso/libSQL SDK. Needed for remote
  SQLite storage. Provides sync and async APIs. No alternative for
  Turso access.

Both are justified per Constitution II (Simplicity/YAGNI) — each
solves a problem that cannot be solved with existing dependencies.
