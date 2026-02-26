"""Payment commands: list, get."""


from typing import Annotated

import typer

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="payments", help="View payments.")

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Status", "status"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Method", "method"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Status", "status"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Method", "method"),
    Column("Order ID", "order_id"),
    Column("Checkout ID", "checkout_id"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_payments(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    order_id: Annotated[str | None, typer.Option("--order-id", help="Filter by order.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List payments."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if order_id:
        kwargs["order_id"] = order_id
    with client:
        res = client.payments.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_payment(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Payment ID.")],
) -> None:
    """Get details for a payment."""
    client = get_client(ctx)
    with client:
        payment = client.payments.get(id=id)
    render_detail(payment, DETAIL_FIELDS, get_output_format(ctx))
