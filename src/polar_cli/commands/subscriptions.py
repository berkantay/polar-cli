"""Subscription commands: list, get, update, revoke."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="subscriptions", help="Manage subscriptions.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Product ID", "product_id"),
    Column("Customer ID", "customer_id"),
    Column("Status", "status"),
    Column("Current Period Start", "current_period_start"),
    Column("Current Period End", "current_period_end"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Product ID", "product_id"),
    Column("Customer ID", "customer_id"),
    Column("Status", "status"),
    Column("Current Period Start", "current_period_start"),
    Column("Current Period End", "current_period_end"),
    Column("Cancel At Period End", "cancel_at_period_end"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_subscriptions(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    product_id: Annotated[str | None, typer.Option("--product-id", help="Filter by product.")] = None,
    active: Annotated[bool | None, typer.Option("--active/--inactive", help="Filter by active status.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List subscriptions."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if product_id:
        kwargs["product_id"] = product_id
    if active is not None:
        kwargs["active"] = active
    with client:
        res = client.subscriptions.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_subscription(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Subscription ID.")],
) -> None:
    """Get details for a subscription."""
    client = get_client(ctx)
    with client:
        sub = client.subscriptions.get(id=id)
    render_detail(sub, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_subscription(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Subscription ID.")],
    product_id: Annotated[str | None, typer.Option("--product-id", help="Change to a different product.")] = None,
    cancel_at_period_end: Annotated[bool | None, typer.Option("--cancel-at-period-end/--no-cancel-at-period-end", help="Cancel at end of current period.")] = None,
) -> None:
    """Update a subscription."""
    update: dict[str, object] = {}
    if product_id is not None:
        update["product_id"] = product_id
    if cancel_at_period_end is not None:
        update["cancel_at_period_end"] = cancel_at_period_end
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        sub = client.subscriptions.update(id=id, subscription_update=update)
    console.print(f"[bold green]Subscription updated:[/bold green] {sub.id}")
    render_detail(sub, DETAIL_FIELDS, get_output_format(ctx))


@app.command("revoke")
@handle_errors
def revoke_subscription(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Subscription ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Revoke (immediately cancel) a subscription."""
    if not yes:
        typer.confirm(f"Revoke subscription {id}? This is immediate and cannot be undone.", abort=True)
    client = get_client(ctx)
    with client:
        sub = client.subscriptions.revoke(id=id)
    console.print(f"[bold green]Subscription revoked:[/bold green] {sub.id}")
    render_detail(sub, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_subscription(
    ctx: typer.Context,
    product_id: Annotated[str, typer.Option("--product-id", help="Product ID.")],
    customer_id: Annotated[str, typer.Option("--customer-id", help="Customer ID.")],
) -> None:
    """Create a free subscription for a customer."""
    client = get_client(ctx)
    request: dict[str, object] = {"product_id": product_id, "customer_id": customer_id}
    with client:
        sub = client.subscriptions.create(request=request)
    console.print(f"[bold green]Subscription created:[/bold green] {sub.id}")
    render_detail(sub, DETAIL_FIELDS, get_output_format(ctx))


@app.command("export")
@handle_errors
def export_subscriptions(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
) -> None:
    """Export subscriptions as CSV."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    with client:
        data = client.subscriptions.export(organization_id=org_id)
    output = data.decode("utf-8") if isinstance(data, bytes) else data
    typer.echo(output)
