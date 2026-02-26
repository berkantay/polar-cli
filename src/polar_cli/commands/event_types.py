"""Event type commands: list, update."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="event-types", help="Manage event types.")
console = Console()

LIST_COLUMNS = [
    Column("Name", "name"),
    Column("Source", "source"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("Name", "name"),
    Column("Source", "source"),
    Column("Created", "created_at"),
    Column("Modified", "modified_at"),
]


@app.command("list")
@handle_errors
def list_event_types(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List event types."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if query:
        kwargs["query"] = query
    with client:
        res = client.event_types.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_event_type(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Event type ID.")],
    is_archived: Annotated[bool | None, typer.Option("--is-archived/--not-archived", help="Archive or unarchive.")] = None,
) -> None:
    """Update an event type."""
    update: dict[str, object] = {}
    if is_archived is not None:
        update["is_archived"] = is_archived
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        result = client.event_types.update(id=id, event_type_update=update)
    console.print("[bold green]Event type updated[/bold green]")
    render_detail(result, DETAIL_FIELDS, get_output_format(ctx))
