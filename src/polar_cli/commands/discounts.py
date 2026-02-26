"""Discount commands: list, get, create, update, delete."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="discounts", help="Manage discounts.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Code", "code"),
    Column("Type", "type"),
    Column("Amount", "amount"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Code", "code"),
    Column("Type", "type"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Duration", "duration"),
    Column("Max Redemptions", "max_redemptions"),
    Column("Redemptions Count", "redemptions_count"),
    Column("Organization ID", "organization_id"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_discounts(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List discounts."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if query:
        kwargs["query"] = query
    with client:
        res = client.discounts.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_discount(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Discount ID.")],
) -> None:
    """Get details for a discount."""
    client = get_client(ctx)
    with client:
        discount = client.discounts.get(id=id)
    render_detail(discount, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_discount(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", help="Discount name.")],
    type: Annotated[str, typer.Option("--type", help="Discount type: percentage or fixed.")],
    amount: Annotated[int, typer.Option("--amount", help="For percentage: 1-100 (percent off). For fixed: cents.")],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    code: Annotated[str | None, typer.Option("--code", help="Coupon code.")] = None,
    duration: Annotated[str, typer.Option("--duration", help="Duration: once, forever, or repeating.")] = "once",
    duration_in_months: Annotated[int | None, typer.Option("--duration-in-months", help="Months (required if duration=repeating).")] = None,
    currency: Annotated[str, typer.Option("--currency", help="Currency for fixed discounts.")] = "usd",
    max_redemptions: Annotated[int | None, typer.Option("--max-redemptions", help="Max number of uses.")] = None,
) -> None:
    """Create a discount."""
    request: dict[str, object] = {
        "name": name,
        "type": type,
        "duration": duration,
    }
    # API expects basis_points for percentage, amount+currency for fixed
    if type == "percentage":
        request["basis_points"] = amount * 100  # Convert percent to basis points
    else:
        request["amount"] = amount
        request["currency"] = currency
    if duration == "repeating" and duration_in_months:
        request["duration_in_months"] = duration_in_months
    if org:
        request["organization_id"] = org
    if code:
        request["code"] = code
    if max_redemptions is not None:
        request["max_redemptions"] = max_redemptions
    client = get_client(ctx)
    with client:
        discount = client.discounts.create(request=request)
    console.print(f"[bold green]Discount created:[/bold green] {discount.id}")
    render_detail(discount, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_discount(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Discount ID.")],
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None,
    code: Annotated[str | None, typer.Option("--code", help="New code.")] = None,
    max_redemptions: Annotated[int | None, typer.Option("--max-redemptions", help="New max redemptions.")] = None,
) -> None:
    """Update a discount."""
    update: dict[str, object] = {}
    if name is not None:
        update["name"] = name
    if code is not None:
        update["code"] = code
    if max_redemptions is not None:
        update["max_redemptions"] = max_redemptions
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        discount = client.discounts.update(id=id, discount_update=update)
    console.print(f"[bold green]Discount updated:[/bold green] {discount.id}")
    render_detail(discount, DETAIL_FIELDS, get_output_format(ctx))


@app.command("delete")
@handle_errors
def delete_discount(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Discount ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a discount."""
    if not yes:
        typer.confirm(f"Delete discount {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.discounts.delete(id=id)
    console.print(f"[bold green]Discount deleted:[/bold green] {id}")
