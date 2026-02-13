from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from movie_buddy.auth import KinoPubAuth
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
