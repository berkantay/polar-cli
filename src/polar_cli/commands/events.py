"""Event commands: list, get, names, ingest."""


import json
from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="events", help="Manage events.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Source", "source"),
    Column("Customer ID", "customer_id"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Source", "source"),
    Column("Customer ID", "customer_id"),
    Column("External Customer ID", "external_customer_id"),
    Column("Metadata", "metadata"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_events(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    customer_id: Annotated[str | None, typer.Option("--customer-id", help="Filter by customer.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List events."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if customer_id:
        kwargs["customer_id"] = customer_id
    if query:
        kwargs["query"] = query
    with client:
        res = client.events.list(**kwargs)
    render_list(res.items, LIST_COLUMNS, res.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_event(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Event ID.")],
) -> None:
    """Get details for an event."""
    client = get_client(ctx)
    with client:
        event = client.events.get(id=id)
    render_detail(event, DETAIL_FIELDS, get_output_format(ctx))


NAME_COLUMNS = [
    Column("Name", "name"),
    Column("Source", "source"),
]


@app.command("names")
@handle_errors
def list_names(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List distinct event names."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if query:
        kwargs["query"] = query
    with client:
        res = client.events.list_names(**kwargs)
    render_list(res.items, NAME_COLUMNS, res.pagination, get_output_format(ctx))


@app.command("ingest")
@handle_errors
def ingest_events(
    ctx: typer.Context,
    events_json: Annotated[str, typer.Argument(help="JSON array of events to ingest.")],
) -> None:
    """Ingest events from a JSON array."""
    parsed = json.loads(events_json)
    client = get_client(ctx)
    with client:
        client.events.ingest(request={"events": parsed})
    console.print(f"[bold green]Ingested {len(parsed)} event(s).[/bold green]")
