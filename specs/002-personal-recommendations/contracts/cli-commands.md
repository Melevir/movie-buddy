# CLI Command Contracts

## movie-buddy rate

Present movies from watching history for the user to rate.

```
Usage: movie-buddy rate [OPTIONS]

Options:
  --help  Show this message and exit

Exit codes:
  0  Rating session completed (all presented or user quit)
  1  Auth required / network error / no watching history
```

**Behavior**:
1. Validate auth token (refresh if needed).
2. Fetch watching history from kino.pub (serials + movies).
3. Load existing ratings from Turso.
4. Filter out already-rated items.
5. If no unrated items remain: print "No more movies to rate.
   Watch more content on kino.pub!" Exit 0.
6. Present up to 10 unrated items one at a time:
   - Show title, year, type in a Rich panel.
   - Prompt: "Rate 1-10 (or Enter to skip): "
   - Valid input (1-10): save rating to Turso, show next.
   - Empty / "s": skip, show next.
   - "q": quit session early. Exit 0.
   - Invalid input: re-prompt.
7. After all items: print summary "Rated X movies. Total ratings: Y."

---

## movie-buddy recommend \<description\>

Get 3 personalized movie/series recommendations.

```
Usage: movie-buddy recommend [OPTIONS] DESCRIPTION

Arguments:
  DESCRIPTION  Natural language description of what you want to
               watch [required]

Options:
  --help  Show this message and exit

Exit codes:
  0  Recommendations displayed (and optionally opened)
  1  Auth required / network error / not enough ratings /
     empty catalog / LLM error
```

**Behavior**:
1. Validate auth token.
2. Load ratings from Turso. If fewer than 5: print "You need at
   least 5 ratings. Run `movie-buddy rate` first." Exit 1.
3. Load catalog from Turso. If empty: print "Catalog is empty.
   Run `movie-buddy catalog` first." Exit 1.
4. Build taste profile from ratings (title + score list).
5. Send to LLM: taste profile + catalog + description.
6. Show progress spinner: "Generating recommendations..."
7. Display 3 recommendations as a Rich numbered table:
   | # | Title | Year | Type | Why |
8. Prompt: "Pick a number to open in Chrome (or Enter to skip): "
   - Valid number (1-3): open in Chrome via existing watch flow.
   - Empty/Enter: exit 0.

---

## movie-buddy catalog

Fetch content from kino.pub and grow the recommendation catalog.

```
Usage: movie-buddy catalog [OPTIONS]

Options:
  --help  Show this message and exit

Exit codes:
  0  Catalog updated successfully
  1  Auth required / network error / storage error
```

**Behavior**:
1. Validate auth token.
2. For each category (fresh, hot, popular) and each type
   (movie, serial, tvshow) — 9 API calls:
   - Fetch `GET /v1/items/{category}?type={type}&perpage=50`
   - Show progress: "Fetching {category}/{type}..."
3. Deduplicate against existing catalog entries (by ID).
4. Insert new entries into Turso catalog table.
5. Print summary:
   - "Catalog updated: X new entries added."
   - "Total catalog size: Y items."

---

## movie-buddy ratings

View all saved ratings.

```
Usage: movie-buddy ratings [OPTIONS]

Options:
  --clear  Remove all ratings after confirmation
  --help   Show this message and exit

Exit codes:
  0  Ratings displayed or cleared
  1  Auth required / storage error
```

**Behavior**:
1. If `--clear`:
   - Prompt: "Remove all ratings? (y/N): "
   - If "y": delete all ratings from Turso, print "All ratings
     cleared." Exit 0.
   - Otherwise: print "Cancelled." Exit 0.
2. Load ratings from Turso.
3. If no ratings: print "No ratings yet. Run `movie-buddy rate`
   to get started." Exit 0.
4. Display Rich table sorted by score (highest first):
   | Title | Type | Score | Rated |
5. Print total: "X movies rated."
