"""Shared helpers — org resolution, spinners."""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

import typer
from rich.console import Console
from rich.status import Status

from polar_cli.config import OutputFormat, get_default_org_id
from polar_cli.context import get_cli_context

if TYPE_CHECKING:
    from polar_sdk import Polar
    from polar_sdk.models import Organization

console = Console(stderr=True)

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def is_uuid(value: str) -> bool:
    """Check if a string looks like a UUID."""
    return bool(UUID_RE.match(value))


def get_org_by_id_or_slug(client: "Polar", id_or_slug: str) -> "Organization":
    """Resolve an organization by ID (UUID) or slug.

    If the input looks like a UUID, fetches directly by ID.
    Otherwise, searches by slug using the list endpoint.

    Raises typer.Exit(1) if not found.
    """
    if is_uuid(id_or_slug):
        return client.organizations.get(id=id_or_slug)

    # Look up by slug
    result = client.organizations.list(slug=id_or_slug, limit=1)
    if result and result.result.items:
        return result.result.items[0]

    console.print(f"[bold red]Organization not found:[/bold red] {id_or_slug}")
    raise typer.Exit(1)


def resolve_org_id(ctx: typer.Context, org_flag: str | None) -> str:
    """Resolve the organization ID from the --org flag or default config.

    Returns the org ID string. Exits with error if neither is available.
    """
    if org_flag:
        return org_flag

    cli_ctx = get_cli_context(ctx)
    default = get_default_org_id(cli_ctx.environment)
    if default:
        return default

    console.print(
        "[bold red]No organization specified.[/bold red] "
        "Pass [bold]--org <id>[/bold] or set a default with [bold]polar org set-default <id>[/bold]."
    )
    raise typer.Exit(1)


@contextmanager
def spinner(message: str) -> Generator[Status, None, None]:
    """Show a spinner while a long operation runs."""
    with console.status(message, spinner="dots") as status:
        yield status


def get_output_format(ctx: typer.Context) -> OutputFormat:
    return get_cli_context(ctx).output_format
