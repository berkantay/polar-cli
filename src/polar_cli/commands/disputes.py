"""Dispute commands: list, get."""


from typing import Annotated

import typer

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="disputes", help="View disputes.")

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Order ID", "order_id"),
    Column("Status", "dispute_status"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Order ID", "order_id"),
    Column("Status", "dispute_status"),
    Column("Reason", "dispute_reason"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_disputes(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    order_id: Annotated[str | None, typer.Option("--order-id", help="Filter by order.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List disputes."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if order_id:
        kwargs["order_id"] = order_id
    with client:
        res = client.disputes.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_dispute(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Dispute ID.")],
) -> None:
    """Get details for a dispute."""
    client = get_client(ctx)
    with client:
        dispute = client.disputes.get(id=id)
    render_detail(dispute, DETAIL_FIELDS, get_output_format(ctx))
