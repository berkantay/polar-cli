"""Order commands: list, get, invoice."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="orders", help="Manage orders.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Product ID", "product_id"),
    Column("Customer ID", "customer_id"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Product ID", "product_id"),
    Column("Customer ID", "customer_id"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Tax Amount", "tax_amount"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_orders(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    product_id: Annotated[str | None, typer.Option("--product-id", help="Filter by product.")] = None,
    customer_id: Annotated[str | None, typer.Option("--customer-id", help="Filter by customer.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List orders."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if product_id:
        kwargs["product_id"] = product_id
    if customer_id:
        kwargs["customer_id"] = customer_id
    with client:
        res = client.orders.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_order(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Order ID.")],
) -> None:
    """Get details for an order."""
    client = get_client(ctx)
    with client:
        order = client.orders.get(id=id)
    render_detail(order, DETAIL_FIELDS, get_output_format(ctx))


@app.command("invoice")
@handle_errors
def get_invoice(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Order ID.")],
) -> None:
    """Get the invoice URL for an order."""
    client = get_client(ctx)
    with client:
        invoice = client.orders.invoice(id=id)
    console.print(f"[bold]Invoice URL:[/bold] {invoice.url}")


@app.command("generate-invoice")
@handle_errors
def generate_invoice(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Order ID.")],
) -> None:
    """Generate a new invoice for an order."""
    client = get_client(ctx)
    with client:
        client.orders.generate_invoice(id=id)
    console.print(f"[bold green]Invoice generated for order:[/bold green] {id}")


@app.command("update")
@handle_errors
def update_order(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Order ID.")],
    billing_name: Annotated[str | None, typer.Option("--billing-name", help="Billing name.")] = None,
) -> None:
    """Update an order."""
    update: dict[str, object] = {}
    if billing_name is not None:
        update["billing_name"] = billing_name
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        order = client.orders.update(id=id, order_update=update)
    console.print(f"[bold green]Order updated:[/bold green] {order.id}")
    render_detail(order, DETAIL_FIELDS, get_output_format(ctx))


@app.command("export")
@handle_errors
def export_orders(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
) -> None:
    """Export orders as CSV."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    with client:
        data = client.orders.export(organization_id=org_id)
    output = data.decode("utf-8") if isinstance(data, bytes) else data
    typer.echo(output)
