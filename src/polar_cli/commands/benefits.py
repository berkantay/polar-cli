"""Benefit commands: list, get, create, update, delete, grants."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="benefits", help="Manage benefits.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Type", "type"),
    Column("Description", "description"),
    Column("Selectable", "selectable"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Type", "type"),
    Column("Description", "description"),
    Column("Selectable", "selectable"),
    Column("Deletable", "deletable"),
    Column("Organization ID", "organization_id"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_benefits(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List benefits."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if query:
        kwargs["query"] = query
    with client:
        res = client.benefits.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_benefit(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Benefit ID.")],
) -> None:
    """Get details for a benefit."""
    client = get_client(ctx)
    with client:
        benefit = client.benefits.get(id=id)
    render_detail(benefit, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_benefit(
    ctx: typer.Context,
    description: Annotated[str, typer.Option("--description", help="Benefit description.")],
    type: Annotated[str, typer.Option("--type", help="Benefit type: custom, discord, downloadables, github_repository, license_keys, meter_credit.")] = "custom",
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    selectable: Annotated[bool, typer.Option("--selectable/--not-selectable", help="Whether customers can select this.")] = False,
    is_tax_applicable: Annotated[bool, typer.Option("--tax-applicable/--not-tax-applicable", help="Whether this benefit is tax applicable.")] = False,
    properties_json: Annotated[str | None, typer.Option("--properties", help="Type-specific properties as JSON.")] = None,
) -> None:
    """Create a benefit (defaults to custom type).

    For types other than 'custom', pass type-specific properties via --properties JSON.
    """
    request: dict[str, object] = {
        "type": type,
        "description": description,
        "selectable": selectable,
        "is_tax_applicable": is_tax_applicable,
    }
    if org:
        request["organization_id"] = org
    if properties_json:
        import json
        request["properties"] = json.loads(properties_json)
    elif type == "custom":
        request["properties"] = {"note": None}
    else:
        request["properties"] = {}
    client = get_client(ctx)
    with client:
        benefit = client.benefits.create(request=request)
    console.print(f"[bold green]Benefit created:[/bold green] {benefit.id}")
    render_detail(benefit, DETAIL_FIELDS, get_output_format(ctx))


@app.command("delete")
@handle_errors
def delete_benefit(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Benefit ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a benefit."""
    if not yes:
        typer.confirm(f"Delete benefit {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.benefits.delete(id=id)
    console.print(f"[bold green]Benefit deleted:[/bold green] {id}")


@app.command("update")
@handle_errors
def update_benefit(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Benefit ID.")],
    description: Annotated[str | None, typer.Option("--description", help="New description.")] = None,
) -> None:
    """Update a benefit."""
    update: dict[str, object] = {}
    if description is not None:
        update["description"] = description
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        benefit = client.benefits.update(id=id, request_body=update)
    console.print(f"[bold green]Benefit updated:[/bold green] {benefit.id}")
    render_detail(benefit, DETAIL_FIELDS, get_output_format(ctx))


GRANT_COLUMNS = [
    Column("ID", "id"),
    Column("Benefit ID", "benefit_id"),
    Column("Customer ID", "customer_id"),
    Column("Is Granted", "is_granted"),
    Column("Created", "created_at"),
]


@app.command("grants")
@handle_errors
def list_grants(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Benefit ID.")],
    is_granted: Annotated[bool | None, typer.Option("--granted/--revoked", help="Filter by grant status.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List grants for a benefit."""
    client = get_client(ctx)
    kwargs: dict[str, object] = {"id": id, "page": page, "limit": limit}
    if is_granted is not None:
        kwargs["is_granted"] = is_granted
    with client:
        res = client.benefits.grants(**kwargs)
    render_list(res.result.items, GRANT_COLUMNS, res.result.pagination, get_output_format(ctx))
