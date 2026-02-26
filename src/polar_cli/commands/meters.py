"""Meter commands: list, get, create, update."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="meters", help="Manage usage meters.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Filter", "filter"),
    Column("Aggregation", "aggregation"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Filter", "filter"),
    Column("Aggregation", "aggregation"),
    Column("Organization ID", "organization_id"),
    Column("Created", "created_at"),
    Column("Modified", "modified_at"),
]


@app.command("list")
@handle_errors
def list_meters(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List meters."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if query:
        kwargs["query"] = query
    with client:
        res = client.meters.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_meter(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Meter ID.")],
) -> None:
    """Get details for a meter."""
    client = get_client(ctx)
    with client:
        meter = client.meters.get(id=id)
    render_detail(meter, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_meter(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", help="Meter name.")],
    filter_json: Annotated[str, typer.Option("--filter", help='Event filter JSON. Example: \'{"conjunction": "and", "clauses": [{"property": "type", "operator": "eq", "value": "api_call"}]}\'')],
    aggregation: Annotated[str, typer.Option("--aggregation", help='Aggregation JSON. Example: \'{"func": "count"}\' or \'{"func": "sum", "property": "amount"}\'')],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
) -> None:
    """Create a meter."""
    import json

    request: dict[str, object] = {
        "name": name,
        "filter": json.loads(filter_json),
        "aggregation": json.loads(aggregation),
    }
    if org:
        request["organization_id"] = org
    client = get_client(ctx)
    with client:
        meter = client.meters.create(request=request)
    console.print(f"[bold green]Meter created:[/bold green] {meter.id}")
    render_detail(meter, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_meter(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Meter ID.")],
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None,
) -> None:
    """Update a meter."""
    update: dict[str, object] = {}
    if name is not None:
        update["name"] = name
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        meter = client.meters.update(id=id, meter_update=update)
    console.print(f"[bold green]Meter updated:[/bold green] {meter.id}")
    render_detail(meter, DETAIL_FIELDS, get_output_format(ctx))


@app.command("quantities")
@handle_errors
def get_quantities(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Meter ID.")],
    start_timestamp: Annotated[str, typer.Option("--start", help="Start timestamp (ISO 8601).")],
    end_timestamp: Annotated[str, typer.Option("--end", help="End timestamp (ISO 8601).")],
    interval: Annotated[str, typer.Option("--interval", help="Interval: hour, day, week, month, year.")] = "day",
) -> None:
    """Get meter quantities over a time range."""
    import datetime as dt

    client = get_client(ctx)
    with client:
        result = client.meters.quantities(
            id=id,
            start_timestamp=dt.datetime.fromisoformat(start_timestamp),
            end_timestamp=dt.datetime.fromisoformat(end_timestamp),
            interval=interval,
        )
    render_detail(result, [], get_output_format(ctx))
