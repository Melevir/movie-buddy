# CLI Command Contracts

## movie-buddy auth

Authenticate with kino.pub via OAuth2 Device Flow.

```
Usage: movie-buddy auth [OPTIONS]

Options:
  --force  Re-authenticate even if a valid token exists
  --help   Show this message and exit

Exit codes:
  0  Authentication successful
  1  Authentication failed or timed out
```

**Behavior**:
1. If valid token exists and `--force` not set: print "Already
   authenticated" and exit 0.
2. Request device code from API.
3. Display: "Go to https://kino.pub/device and enter code: XXXXX"
4. Poll for token at interval (show spinner).
5. On success: encrypt and store token, print "Authenticated
   successfully".
6. On timeout (300s): print error, exit 1.

---

## movie-buddy watch \<name\>

Open a random episode of the given series (or movie page) in Chrome.

```
Usage: movie-buddy watch [OPTIONS] NAME

Arguments:
  NAME  Movie or series name to search for [required]

Options:
  --help  Show this message and exit

Exit codes:
  0  Browser opened successfully
  1  No results found / auth required / network error
  2  Chrome not found
```

**Behavior**:
1. Validate auth token (refresh if needed).
2. Search kino.pub for NAME (filtered to movie/serial/tvshow).
3. If 0 results: print "No results found for '{NAME}'. Check
   spelling and try again." Exit 1.
4. If 1 result: use it.
5. If multiple results:
   a. Fetch watching list + bookmarks.
   b. If exactly 1 search result is in watching/bookmarks:
      auto-select it, print "Auto-selected: {title} (in your
      watching list)".
   c. Otherwise: display top 5 as numbered list, prompt user to
      pick (1-5).
6. If selected content is series/tvshow:
   a. Fetch item details (with `nolinks=1`).
   b. Flatten all episodes, pick uniformly at random.
   c. Print formatted panel: title, S##E##, episode title.
   d. Open `https://kino.pub/item/view/{id}/s{S}e{E}` in Chrome.
7. If selected content is movie:
   a. Print formatted panel: title, year.
   b. Open `https://kino.pub/item/view/{id}` in Chrome.

---

## movie-buddy search \<name\> (development/debug only)

Search kino.pub and display results. May be removed before release.

```
Usage: movie-buddy search [OPTIONS] NAME

Arguments:
  NAME  Search query [required]

Options:
  --help  Show this message and exit
```
