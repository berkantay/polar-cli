"""Custom field commands: list, get, create, update, delete."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="custom-fields", help="Manage custom fields.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Slug", "slug"),
    Column("Name", "name"),
    Column("Type", "type"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Slug", "slug"),
    Column("Name", "name"),
    Column("Type", "type"),
    Column("Properties", "properties"),
    Column("Organization ID", "organization_id"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_custom_fields(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List custom fields."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if query:
        kwargs["query"] = query
    with client:
        res = client.custom_fields.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_custom_field(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Custom field ID.")],
) -> None:
    """Get details for a custom field."""
    client = get_client(ctx)
    with client:
        field = client.custom_fields.get(id=id)
    render_detail(field, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_custom_field(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", help="Field name.")],
    slug: Annotated[str, typer.Option("--slug", help="Field slug (URL-friendly identifier).")],
    type: Annotated[str, typer.Option("--type", help="Field type: text, number, date, checkbox, select.")] = "text",
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    properties_json: Annotated[str | None, typer.Option("--properties", help="Type-specific properties as JSON (e.g. select options).")] = None,
) -> None:
    """Create a custom field."""
    import json as json_mod

    request: dict[str, object] = {
        "type": type,
        "name": name,
        "slug": slug,
        "properties": json_mod.loads(properties_json) if properties_json else {},
    }
    if org:
        request["organization_id"] = org
    client = get_client(ctx)
    with client:
        field = client.custom_fields.create(request=request)
    console.print(f"[bold green]Custom field created:[/bold green] {field.id}")
    render_detail(field, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_custom_field(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Custom field ID.")],
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None,
) -> None:
    """Update a custom field."""
    if name is None:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    # The update is type-discriminated in the SDK; we need to know the type first
    client = get_client(ctx)
    with client:
        existing = client.custom_fields.get(id=id)
        field_type = getattr(existing, "type", "text")
        update: dict[str, object] = {"type": field_type, "name": name}
        field = client.custom_fields.update(id=id, custom_field_update=update)
    console.print(f"[bold green]Custom field updated:[/bold green] {field.id}")
    render_detail(field, DETAIL_FIELDS, get_output_format(ctx))


@app.command("delete")
@handle_errors
def delete_custom_field(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Custom field ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a custom field."""
    if not yes:
        typer.confirm(f"Delete custom field {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.custom_fields.delete(id=id)
    console.print(f"[bold green]Custom field deleted:[/bold green] {id}")
