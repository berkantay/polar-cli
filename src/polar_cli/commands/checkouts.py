"""Checkout commands: list, get, create, update."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="checkouts", help="Manage checkout sessions.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Product ID", "product_id"),
    Column("Status", "status"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Product ID", "product_id"),
    Column("Customer ID", "customer_id"),
    Column("Status", "status"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("URL", "url"),
    Column("Success URL", "success_url"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_checkouts(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    product_id: Annotated[str | None, typer.Option("--product-id", help="Filter by product.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List checkout sessions."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if product_id:
        kwargs["product_id"] = product_id
    with client:
        res = client.checkouts.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_checkout(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Checkout ID.")],
) -> None:
    """Get details for a checkout session."""
    client = get_client(ctx)
    with client:
        checkout = client.checkouts.get(id=id)
    render_detail(checkout, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_checkout(
    ctx: typer.Context,
    product_ids: Annotated[list[str], typer.Option("--product", help="Product ID (can specify multiple).")],
    success_url: Annotated[str | None, typer.Option("--success-url", help="Redirect after checkout.")] = None,
    customer_email: Annotated[str | None, typer.Option("--customer-email", help="Pre-fill customer email.")] = None,
    discount_id: Annotated[str | None, typer.Option("--discount-id", help="Discount ID to apply.")] = None,
) -> None:
    """Create a checkout session."""
    request: dict[str, object] = {"products": product_ids}
    if success_url:
        request["success_url"] = success_url
    if customer_email:
        request["customer_email"] = customer_email
    if discount_id:
        request["discount_id"] = discount_id
    client = get_client(ctx)
    with client:
        checkout = client.checkouts.create(request=request)
    console.print(f"[bold green]Checkout created:[/bold green] {checkout.url}")
    render_detail(checkout, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_checkout(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Checkout ID.")],
    customer_email: Annotated[str | None, typer.Option("--customer-email", help="New customer email.")] = None,
) -> None:
    """Update a checkout session."""
    update: dict[str, object] = {}
    if customer_email is not None:
        update["customer_email"] = customer_email
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        checkout = client.checkouts.update(id=id, checkout_update=update)
    console.print(f"[bold green]Checkout updated:[/bold green] {checkout.id}")
    render_detail(checkout, DETAIL_FIELDS, get_output_format(ctx))
