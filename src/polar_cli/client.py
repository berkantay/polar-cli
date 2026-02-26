"""Polar SDK client factory — reads token from config, creates client."""

from __future__ import annotations

import typer
from polar_sdk import Polar
from rich.console import Console

from polar_cli.config import Environment, get_token
from polar_cli.context import CliContext, get_cli_context

console = Console(stderr=True)

# Base URLs for manual HTTP calls (e.g. SSE listener)
SERVER_URLS: dict[Environment, str] = {
    Environment.PRODUCTION: "https://api.polar.sh",
    Environment.SANDBOX: "https://sandbox-api.polar.sh",
}


def get_client(ctx: typer.Context) -> Polar:
    """Create a Polar SDK client from the current CLI context."""
    cli_ctx = get_cli_context(ctx)
    token = _require_token(cli_ctx)

    if cli_ctx.base_url:
        return Polar(access_token=token, server_url=cli_ctx.base_url)

    server = "sandbox" if cli_ctx.sandbox else "production"
    return Polar(access_token=token, server=server)


def get_base_url(ctx: typer.Context) -> str:
    """Get the API base URL for direct HTTP calls (e.g. SSE)."""
    cli_ctx = get_cli_context(ctx)
    if cli_ctx.base_url:
        return cli_ctx.base_url.rstrip("/")
    return SERVER_URLS[cli_ctx.environment]


def require_token(ctx: typer.Context) -> str:
    """Get the access token or exit with an error."""
    cli_ctx = get_cli_context(ctx)
    return _require_token(cli_ctx)


def _require_token(cli_ctx: CliContext) -> str:
    token = get_token(cli_ctx.environment)
    if token is None:
        sandbox_flag = " --sandbox" if cli_ctx.sandbox else ""
        console.print(
            f"[bold red]Not authenticated.[/bold red] "
            f"Run [bold]polar auth login{sandbox_flag}[/bold] first."
        )
        raise typer.Exit(1)
    return token
