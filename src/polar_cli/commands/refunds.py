"""Refund commands: list, create."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="refunds", help="Manage refunds.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Order ID", "order_id"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Reason", "reason"),
    Column("Succeeded", "succeeded"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Order ID", "order_id"),
    Column("Subscription ID", "subscription_id"),
    Column("Customer ID", "customer_id"),
    Column("Amount", "amount"),
    Column("Currency", "currency"),
    Column("Reason", "reason"),
    Column("Comment", "comment"),
    Column("Succeeded", "succeeded"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_refunds(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    order_id: Annotated[str | None, typer.Option("--order-id", help="Filter by order.")] = None,
    customer_id: Annotated[str | None, typer.Option("--customer-id", help="Filter by customer.")] = None,
    succeeded: Annotated[bool | None, typer.Option("--succeeded/--failed", help="Filter by status.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List refunds."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if order_id:
        kwargs["order_id"] = order_id
    if customer_id:
        kwargs["customer_id"] = customer_id
    if succeeded is not None:
        kwargs["succeeded"] = succeeded
    with client:
        res = client.refunds.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_refund(
    ctx: typer.Context,
    order_id: Annotated[str, typer.Option("--order-id", help="Order ID to refund.")],
    reason: Annotated[str, typer.Option("--reason", help="Reason: duplicate, fraudulent, customer_request, service_disruption, other.")] = "customer_request",
    amount: Annotated[int | None, typer.Option("--amount", help="Partial refund amount in cents. Omit for full refund.")] = None,
    comment: Annotated[str | None, typer.Option("--comment", help="Internal comment.")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Create a refund for an order."""
    if not yes:
        typer.confirm(f"Refund order {order_id}?", abort=True)
    request: dict[str, object] = {"order_id": order_id, "reason": reason}
    if amount is not None:
        request["amount"] = amount
    if comment:
        request["comment"] = comment
    client = get_client(ctx)
    with client:
        refund = client.refunds.create(request=request)
    console.print(f"[bold green]Refund created:[/bold green] {refund.id}")
    render_detail(refund, DETAIL_FIELDS, get_output_format(ctx))
