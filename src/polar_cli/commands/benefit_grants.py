"""Benefit grant commands: list."""


from typing import Annotated

import typer

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="benefit-grants", help="View benefit grants.")

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Benefit ID", "benefit_id"),
    Column("Customer ID", "customer_id"),
    Column("Is Granted", "is_granted"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_benefit_grants(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    customer_id: Annotated[str | None, typer.Option("--customer-id", help="Filter by customer.")] = None,
    is_granted: Annotated[bool | None, typer.Option("--granted/--revoked", help="Filter by grant status.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List benefit grants."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if customer_id:
        kwargs["customer_id"] = customer_id
    if is_granted is not None:
        kwargs["is_granted"] = is_granted
    with client:
        res = client.benefit_grants.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))
