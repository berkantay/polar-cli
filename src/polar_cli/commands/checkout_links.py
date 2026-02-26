"""Checkout link commands: list, get, create, update, delete."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="checkout-links", help="Manage checkout links.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Product ID", "product_id"),
    Column("URL", "url"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Product ID", "product_id"),
    Column("URL", "url"),
    Column("Success URL", "success_url"),
    Column("Label", "label"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_checkout_links(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    product_id: Annotated[str | None, typer.Option("--product-id", help="Filter by product.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List checkout links."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if product_id:
        kwargs["product_id"] = product_id
    with client:
        res = client.checkout_links.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_checkout_link(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Checkout link ID.")],
) -> None:
    """Get details for a checkout link."""
    client = get_client(ctx)
    with client:
        link = client.checkout_links.get(id=id)
    render_detail(link, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_checkout_link(
    ctx: typer.Context,
    product_id: Annotated[str, typer.Option("--product-id", help="Product ID.")],
    success_url: Annotated[str | None, typer.Option("--success-url", help="Redirect URL after checkout.")] = None,
    label: Annotated[str | None, typer.Option("--label", help="Internal label.")] = None,
) -> None:
    """Create a checkout link."""
    request: dict[str, object] = {"product_id": product_id}
    if success_url:
        request["success_url"] = success_url
    if label:
        request["label"] = label
    client = get_client(ctx)
    with client:
        link = client.checkout_links.create(request=request)
    console.print(f"[bold green]Checkout link created:[/bold green] {link.url}")
    render_detail(link, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_checkout_link(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Checkout link ID.")],
    label: Annotated[str | None, typer.Option("--label", help="New label.")] = None,
    success_url: Annotated[str | None, typer.Option("--success-url", help="New success URL.")] = None,
) -> None:
    """Update a checkout link."""
    update: dict[str, object] = {}
    if label is not None:
        update["label"] = label
    if success_url is not None:
        update["success_url"] = success_url
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        link = client.checkout_links.update(id=id, checkout_link_update=update)
    console.print(f"[bold green]Checkout link updated:[/bold green] {link.id}")
    render_detail(link, DETAIL_FIELDS, get_output_format(ctx))


@app.command("delete")
@handle_errors
def delete_checkout_link(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Checkout link ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a checkout link."""
    if not yes:
        typer.confirm(f"Delete checkout link {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.checkout_links.delete(id=id)
    console.print(f"[bold green]Checkout link deleted:[/bold green] {id}")
