"""Organization commands: list, get, set-default."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.config import set_default_org_id
from polar_cli.context import get_cli_context
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_org_by_id_or_slug, get_output_format

app = typer.Typer(name="org", help="Manage organizations.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Slug", "slug"),
    Column("Name", "name"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Slug", "slug"),
    Column("Name", "name"),
    Column("Avatar URL", "avatar_url"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_orgs(
    ctx: typer.Context,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List organizations you have access to."""
    client = get_client(ctx)
    with client:
        res = client.organizations.list(page=page, limit=limit)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_org(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Organization ID or slug.")],
) -> None:
    """Get details for an organization."""
    client = get_client(ctx)
    with client:
        org = get_org_by_id_or_slug(client, id)
    render_detail(org, DETAIL_FIELDS, get_output_format(ctx))


@app.command("set-default")
@handle_errors
def set_default(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Organization ID or slug to set as default.")],
) -> None:
    """Set the default organization for commands."""
    cli_ctx = get_cli_context(ctx)
    client = get_client(ctx)

    with client:
        org = get_org_by_id_or_slug(client, id)

    set_default_org_id(cli_ctx.environment, str(org.id))
    console.print(f"[bold green]Default organization set:[/bold green] {org.name} ({org.slug})")


@app.command("create")
@handle_errors
def create_org(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", help="Organization name.")],
    slug: Annotated[str | None, typer.Option("--slug", help="URL slug.")] = None,
) -> None:
    """Create a new organization."""
    client = get_client(ctx)
    request: dict[str, object] = {"name": name}
    if slug:
        request["slug"] = slug
    with client:
        org = client.organizations.create(request=request)
    console.print(f"[bold green]Organization created:[/bold green] {org.name} ({org.slug})")
    render_detail(org, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_org(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Organization ID or slug.")],
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None,
) -> None:
    """Update an organization."""
    update: dict[str, object] = {}
    if name is not None:
        update["name"] = name
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        org = get_org_by_id_or_slug(client, id)
        org = client.organizations.update(id=str(org.id), organization_update=update)
    console.print(f"[bold green]Organization updated:[/bold green] {org.name} ({org.slug})")
    render_detail(org, DETAIL_FIELDS, get_output_format(ctx))
