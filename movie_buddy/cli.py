from __future__ import annotations

import random

import typer
from rich.console import Console
from rich.panel import Panel

from movie_buddy.api import KinoPubClient
from movie_buddy.auth import KinoPubAuth
from movie_buddy.browser import open_in_chrome
from movie_buddy.models import AuthTimeoutError

app = typer.Typer(name="movie-buddy", help="Open random episodes on kino.pub")
console = Console()


@app.command()
def auth(
    force: bool = typer.Option(False, help="Re-authenticate even if token exists"),
) -> None:
    """Authenticate with kino.pub via OAuth2 Device Flow."""
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


@app.command()
def watch(
    name: str = typer.Argument(help="Movie or series name to search for"),
) -> None:
    """Open a random episode of a series (or movie page) in Chrome."""
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

    selected = results[0]

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
