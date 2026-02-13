from __future__ import annotations

import datetime
import random

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from movie_buddy.api import KinoPubClient
from movie_buddy.auth import KinoPubAuth
from movie_buddy.browser import open_in_chrome
from movie_buddy.matcher import rank_results
from movie_buddy.models import (
    AuthError,
    AuthTimeoutError,
    CatalogEntry,
    Content,
    KinoPubError,
    NetworkError,
    Rating,
    WatchingItem,
)
from movie_buddy.storage import TursoStorage

app = typer.Typer(name="movie-buddy", help="Open random episodes on kino.pub")
console = Console()

TYPE_LABELS: dict[str, str] = {
    "serial": "Series",
    "tvshow": "TV Show",
    "movie": "Movie",
}


@app.command()
def auth(
    force: bool = typer.Option(False, help="Re-authenticate even if token exists"),
) -> None:
    """Authenticate with kino.pub via OAuth2 Device Flow.

    Example: movie-buddy auth
    Example: movie-buddy auth --force
    """
    kinopub_auth = KinoPubAuth()

    if not force:
        token = kinopub_auth.load_token()
        if token is not None and not token.is_expired:
            console.print("[green]Already authenticated.[/green]")
            raise typer.Exit()

    try:
        device_code = kinopub_auth.start_device_flow()
    except Exception as e:
        console.print(
            Panel(
                f"[red]Failed to start authentication:[/red] {e}",
                title="Error",
            )
        )
        raise typer.Exit(code=1) from e

    console.print(
        Panel(
            f"Go to [bold cyan]{device_code.verification_uri}[/bold cyan]\n"
            f"and enter code: [bold yellow]{device_code.user_code}[/bold yellow]",
            title="Authenticate",
        )
    )

    try:
        with console.status("Waiting for authorization..."):
            token = kinopub_auth.poll_for_token(device_code)
    except AuthTimeoutError:
        console.print("[red]Authorization timed out. Please try again.[/red]")
        raise typer.Exit(code=1) from None

    kinopub_auth.save_token(token)
    console.print("[green]Authenticated successfully![/green]")


def _fetch_activity_ids(client: KinoPubClient) -> tuple[set[int], set[int]]:
    watching_ids: set[int] = set()
    bookmark_ids: set[int] = set()

    for item in client.get_watching_serials():
        watching_ids.add(item.id)
    for item in client.get_watching_movies():
        watching_ids.add(item.id)

    for folder in client.get_bookmark_folders():
        for item_id in client.get_bookmark_items(folder.id):
            bookmark_ids.add(item_id)

    return watching_ids, bookmark_ids


def _prompt_picker(results: list[Content]) -> Content:
    top = results[:5]
    table = Table(title="Multiple results found")
    table.add_column("#", style="bold")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Year")
    for i, item in enumerate(top, 1):
        table.add_row(
            str(i),
            item.title,
            TYPE_LABELS.get(item.content_type, item.content_type),
            str(item.year),
        )
    console.print(table)

    while True:
        choice = console.input(f"Pick a number (1-{len(top)}): ")
        if choice.isdigit() and 1 <= int(choice) <= len(top):
            return top[int(choice) - 1]
        console.print(f"[red]Enter a number between 1 and {len(top)}.[/red]")


@app.command()
def watch(
    name: str = typer.Argument(help="Movie or series name to search for"),
) -> None:
    """Open a random episode of a series (or movie page) in Chrome.

    Example: movie-buddy watch "Friends"
    Example: movie-buddy watch "The Matrix"
    """
    try:
        _watch_impl(name)
    except AuthError as e:
        console.print(
            Panel(
                f"[red]Authentication required.[/red]\n"
                f"Please run [bold]movie-buddy auth[/bold] to authenticate.\n"
                f"Details: {e}",
                title="Auth Error",
            )
        )
        raise typer.Exit(code=1) from None
    except NetworkError as e:
        console.print(
            Panel(
                f"[red]Unable to reach kino.pub.[/red]\n"
                f"Check your internet connection and try again.\n"
                f"Details: {e}",
                title="Network Error",
            )
        )
        raise typer.Exit(code=1) from None
    except KinoPubError as e:
        console.print(
            Panel(
                f"[red]An error occurred:[/red] {e}",
                title="Error",
            )
        )
        raise typer.Exit(code=1) from None


def _watch_impl(name: str) -> None:
    kinopub_auth = KinoPubAuth()
    token = kinopub_auth.ensure_valid_token()
    client = KinoPubClient(token)

    with console.status("Searching kino.pub..."):
        results = client.search(name)

    if not results:
        console.print(
            f"[red]No results found for '{name}'. Check spelling and try again.[/red]"
        )
        raise typer.Exit(code=1)

    selected: Content
    if len(results) == 1:
        selected = results[0]
    else:
        with console.status("Checking your activity..."):
            watching_ids, bookmark_ids = _fetch_activity_ids(client)

        matched, reason = rank_results(
            results, watching_ids=watching_ids, bookmark_ids=bookmark_ids
        )
        if matched is not None and reason is not None:
            console.print(f"[cyan]Auto-selected: {reason}[/cyan]")
            selected = matched
        else:
            selected = _prompt_picker(results)

    _open_content(client, selected)


def _open_content(client: KinoPubClient, selected: Content) -> None:
    if selected.content_type == "movie":
        url = selected.build_watch_url()
        console.print(
            Panel(
                f"[bold]{selected.title}[/bold] ({selected.year})",
                title="Movie",
            )
        )
    else:
        with console.status("Fetching episode list..."):
            detailed = client.get_item(selected.id)

        all_episodes = detailed.all_episodes
        if not all_episodes:
            console.print("[red]No episodes found for this series.[/red]")
            raise typer.Exit(code=1)

        episode = random.choice(all_episodes)  # noqa: S311
        url = detailed.build_watch_url(episode)
        console.print(
            Panel(
                f"[bold]{detailed.title}[/bold]\n"
                f"S{episode.season_number:02d}E{episode.number:02d}: {episode.title}",
                title="Random Episode",
            )
        )

    open_in_chrome(url)


@app.command()
def rate() -> None:
    """Rate movies from your kino.pub watching history.

    Example: movie-buddy rate
    """
    try:
        _rate_impl()
    except AuthError as e:
        console.print(
            Panel(
                "[red]Authentication required.[/red]\n"
                "Please run [bold]movie-buddy auth[/bold] to authenticate.\n"
                f"Details: {e}",
                title="Auth Error",
            )
        )
        raise typer.Exit(code=1) from None
    except NetworkError as e:
        console.print(
            Panel(
                "[red]Unable to reach kino.pub.[/red]\n"
                "Check your internet connection and try again.\n"
                f"Details: {e}",
                title="Network Error",
            )
        )
        raise typer.Exit(code=1) from None
    except KinoPubError as e:
        console.print(Panel(f"[red]An error occurred:[/red] {e}", title="Error"))
        raise typer.Exit(code=1) from None


def _rate_impl() -> None:
    kinopub_auth = KinoPubAuth()
    token = kinopub_auth.ensure_valid_token()
    client = KinoPubClient(token)
    storage = TursoStorage()
    storage.init_schema()

    with console.status("Fetching watching history..."):
        watching: list[WatchingItem] = []
        watching.extend(client.get_watching_serials())
        watching.extend(client.get_watching_movies())

    rated_ids = storage.get_rated_content_ids()
    unrated = [w for w in watching if w.id not in rated_ids]

    if not unrated:
        console.print("No more movies to rate. Watch more content on kino.pub!")
        return

    candidates = unrated[:10]
    rated_count = 0

    for item in candidates:
        label = TYPE_LABELS.get(item.content_type, item.content_type)
        console.print(
            Panel(
                f"[bold]{item.title}[/bold] [{label}]",
                title="Rate this",
            )
        )
        while True:
            choice = console.input("Rate 1-10 (or Enter to skip): ")
            choice = choice.strip()
            if choice == "q":
                _print_rate_summary(rated_count, storage)
                return
            if choice in ("", "s"):
                break
            if choice.isdigit() and 1 <= int(choice) <= 10:
                now = datetime.datetime.now(tz=datetime.UTC).isoformat()
                rating = Rating(
                    content_id=item.id,
                    title=item.title,
                    content_type=item.content_type,
                    score=int(choice),
                    rated_at=now,
                )
                storage.insert_ratings([rating])
                rated_count += 1
                break
            console.print(
                "[red]Enter a number 1-10, Enter to skip, or q to quit.[/red]"
            )

    _print_rate_summary(rated_count, storage)


def _print_rate_summary(rated_count: int, storage: TursoStorage) -> None:
    total = len(storage.get_all_ratings())
    console.print(f"Rated {rated_count} movies. Total ratings: {total}.")


_CATALOG_CATEGORIES = ("fresh", "hot", "popular")
_CATALOG_TYPES = ("movie", "serial", "tvshow")


@app.command()
def catalog() -> None:
    """Fetch content from kino.pub and grow the recommendation catalog.

    Example: movie-buddy catalog
    """
    try:
        _catalog_impl()
    except AuthError as e:
        console.print(
            Panel(
                "[red]Authentication required.[/red]\n"
                "Please run [bold]movie-buddy auth[/bold] to authenticate.\n"
                f"Details: {e}",
                title="Auth Error",
            )
        )
        raise typer.Exit(code=1) from None
    except NetworkError as e:
        console.print(
            Panel(
                "[red]Unable to reach kino.pub.[/red]\n"
                "Check your internet connection and try again.\n"
                f"Details: {e}",
                title="Network Error",
            )
        )
        raise typer.Exit(code=1) from None
    except KinoPubError as e:
        console.print(Panel(f"[red]An error occurred:[/red] {e}", title="Error"))
        raise typer.Exit(code=1) from None


def _catalog_impl() -> None:
    kinopub_auth = KinoPubAuth()
    token = kinopub_auth.ensure_valid_token()
    client = KinoPubClient(token)
    storage = TursoStorage()
    storage.init_schema()

    existing_ids = storage.get_existing_catalog_ids()
    all_fetched: list[CatalogEntry] = []

    for cat in _CATALOG_CATEGORIES:
        for ctype in _CATALOG_TYPES:
            console.print(f"Fetching {cat}/{ctype}...")
            entries = client.get_category_items(cat, ctype)
            all_fetched.extend(entries)

    new_entries = [e for e in all_fetched if e.id not in existing_ids]
    # Deduplicate within the batch itself (same item in multiple categories)
    seen: set[int] = set()
    unique_new: list[CatalogEntry] = []
    for entry in new_entries:
        if entry.id not in seen:
            seen.add(entry.id)
            unique_new.append(entry)

    if unique_new:
        storage.insert_catalog_entries(unique_new)

    total = storage.get_catalog_count()
    console.print(
        f"Catalog updated: {len(unique_new)} new entries added.\n"
        f"Total catalog size: {total} items."
    )
