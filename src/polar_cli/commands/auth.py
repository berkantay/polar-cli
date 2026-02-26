"""Auth commands: login, logout, status."""


from typing import Annotated

import typer
from polar_sdk import Polar
from rich.console import Console

from polar_cli.config import Environment, get_token, remove_token, set_token
from polar_cli.context import get_cli_context
from polar_cli.errors import handle_errors

app = typer.Typer(name="auth", help="Authenticate with Polar.")
console = Console()


@app.command()
@handle_errors
def login(
    ctx: typer.Context,
    token: Annotated[
        str | None,
        typer.Option("--token", "-t", help="Personal access token. If omitted, you'll be prompted."),
    ] = None,
) -> None:
    """Log in with a personal access token."""
    cli_ctx = get_cli_context(ctx)

    if token is None:
        settings_url = (
            "https://sandbox.polar.sh/settings"
            if cli_ctx.sandbox
            else "https://polar.sh/settings"
        )
        console.print(f"Create a token at [bold link={settings_url}]{settings_url}[/bold link]")
        token = typer.prompt("Paste your access token")

    # Validate the token by making a test call
    client = _make_client(cli_ctx.environment, cli_ctx.base_url, token)
    with client:
        res = client.organizations.list(page=1, limit=1)
        org_count = res.result.pagination.total_count

    set_token(cli_ctx.environment, token)
    console.print(
        f"[bold green]Logged in[/bold green] to [bold]{cli_ctx.environment.value}[/bold] "
        f"({org_count} organization(s) accessible)"
    )


@app.command()
@handle_errors
def logout(ctx: typer.Context) -> None:
    """Remove the stored access token."""
    cli_ctx = get_cli_context(ctx)

    if get_token(cli_ctx.environment) is None:
        console.print(f"[dim]Not logged in to {cli_ctx.environment.value}.[/dim]")
        raise typer.Exit()

    remove_token(cli_ctx.environment)
    console.print(f"[bold]Logged out[/bold] from [bold]{cli_ctx.environment.value}[/bold].")


@app.command()
@handle_errors
def status(ctx: typer.Context) -> None:
    """Show current authentication status."""
    cli_ctx = get_cli_context(ctx)
    env_label = cli_ctx.environment.value

    token = get_token(cli_ctx.environment)
    if not token:
        console.print(f"[bold]{env_label}:[/bold] [dim]Not authenticated[/dim]")
        raise typer.Exit(1)

    client = _make_client(cli_ctx.environment, cli_ctx.base_url, token)
    with client:
        res = client.organizations.list(page=1, limit=5)
        orgs = res.result.items

    console.print(f"[bold]{env_label}:[/bold] [green]Authenticated[/green]")
    if orgs:
        console.print("Organizations:")
        for org in orgs:
            console.print(f"  - {org.name} ({org.slug})")


def _make_client(env: Environment, base_url: str | None, token: str) -> Polar:
    if base_url:
        return Polar(access_token=token, server_url=base_url)
    server = "sandbox" if env == Environment.SANDBOX else "production"
    return Polar(access_token=token, server=server)
