"""Product commands: list, get, create, update."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="products", help="Manage products.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Is Archived", "is_archived"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Description", "description"),
    Column("Is Archived", "is_archived"),
    Column("Organization ID", "organization_id"),
    Column("Created", "created_at"),
    Column("Modified", "modified_at"),
]


@app.command("list")
@handle_errors
def list_products(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List products."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if query:
        kwargs["query"] = query
    with client:
        res = client.products.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_product(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Product ID.")],
) -> None:
    """Get details for a product."""
    client = get_client(ctx)
    with client:
        product = client.products.get(id=id)
    render_detail(product, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_product(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", help="Product name.")],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    description: Annotated[str | None, typer.Option("--description", help="Product description.")] = None,
    price_amount: Annotated[int | None, typer.Option("--price-amount", help="Price in cents.")] = None,
    price_currency: Annotated[str, typer.Option("--price-currency", help="Currency code.")] = "usd",
    recurring_interval: Annotated[str | None, typer.Option("--recurring-interval", help="Recurring interval: month or year.")] = None,
) -> None:
    """Create a new product."""
    client = get_client(ctx)

    request: dict[str, object] = {
        "name": name,
        "prices": [],
    }
    # Only include organization_id if explicitly provided (org-scoped tokens don't need it)
    if org:
        request["organization_id"] = org
    if description is not None:
        request["description"] = description
    if recurring_interval:
        request["recurring_interval"] = recurring_interval

    if price_amount is not None:
        price: dict[str, object] = {
            "amount_type": "fixed",
            "price_amount": price_amount,
            "price_currency": price_currency,
        }
        if recurring_interval:
            price["type"] = "recurring"
            price["recurring_interval"] = recurring_interval
        else:
            price["type"] = "one_time"
        request["prices"] = [price]

    with client:
        product = client.products.create(request=request)
    console.print(f"[bold green]Product created:[/bold green] {product.id}")
    render_detail(product, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_product(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Product ID.")],
    name: Annotated[str | None, typer.Option("--name", help="New product name.")] = None,
    description: Annotated[str | None, typer.Option("--description", help="New description.")] = None,
    is_archived: Annotated[bool | None, typer.Option("--is-archived", help="Archive or unarchive.")] = None,
) -> None:
    """Update a product."""
    client = get_client(ctx)
    update: dict[str, object] = {}
    if name is not None:
        update["name"] = name
    if description is not None:
        update["description"] = description
    if is_archived is not None:
        update["is_archived"] = is_archived

    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()

    with client:
        product = client.products.update(id=id, product_update=update)
    console.print(f"[bold green]Product updated:[/bold green] {product.id}")
    render_detail(product, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update-benefits")
@handle_errors
def update_benefits(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Product ID.")],
    benefits: Annotated[list[str], typer.Option("--benefit", help="Benefit IDs (repeat for multiple).")],
) -> None:
    """Set the benefits attached to a product."""
    client = get_client(ctx)
    with client:
        product = client.products.update_benefits(
            id=id,
            product_benefits_update={"benefits": [{"benefit_id": b} for b in benefits]},
        )
    console.print(f"[bold green]Benefits updated for product:[/bold green] {product.id}")
    render_detail(product, DETAIL_FIELDS, get_output_format(ctx))
