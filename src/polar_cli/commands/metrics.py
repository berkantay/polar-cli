"""Metrics command: get revenue/subscription analytics."""


import datetime
from typing import Annotated

import typer

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import render_detail
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="metrics", help="View revenue and subscription metrics.")


@app.command("get")
@handle_errors
def get_metrics(
    ctx: typer.Context,
    start_date: Annotated[str, typer.Option("--start-date", help="Start date (YYYY-MM-DD).")],
    end_date: Annotated[str, typer.Option("--end-date", help="End date (YYYY-MM-DD).")],
    interval: Annotated[str, typer.Option("--interval", help="Time interval: day, week, month, year.")] = "month",
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    product_id: Annotated[str | None, typer.Option("--product-id", help="Filter by product.")] = None,
) -> None:
    """Get revenue and subscription metrics for a date range."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {
        "start_date": datetime.date.fromisoformat(start_date),
        "end_date": datetime.date.fromisoformat(end_date),
        "interval": interval,
        "organization_id": org_id,
    }
    if product_id:
        kwargs["product_id"] = product_id
    with client:
        result = client.metrics.get(**kwargs)
    render_detail(result, [], get_output_format(ctx))


@app.command("limits")
@handle_errors
def get_limits(ctx: typer.Context) -> None:
    """Get the available metrics and their limits."""
    client = get_client(ctx)
    with client:
        result = client.metrics.limits()
    render_detail(result, [], get_output_format(ctx))
