"""Customer commands: list, get, create, update, delete."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="customers", help="Manage customers.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Email", "email"),
    Column("Name", "name"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Email", "email"),
    Column("Name", "name"),
    Column("Organization ID", "organization_id"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_customers(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    email: Annotated[str | None, typer.Option("--email", help="Filter by email.")] = None,
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List customers."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if email:
        kwargs["email"] = email
    if query:
        kwargs["query"] = query
    with client:
        res = client.customers.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_customer(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Customer ID.")],
) -> None:
    """Get details for a customer."""
    client = get_client(ctx)
    with client:
        customer = client.customers.get(id=id)
    render_detail(customer, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_customer(
    ctx: typer.Context,
    email: Annotated[str, typer.Option("--email", help="Customer email.")],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    name: Annotated[str | None, typer.Option("--name", help="Customer name.")] = None,
) -> None:
    """Create a new customer."""
    client = get_client(ctx)
    request: dict[str, object] = {"email": email}
    if org:
        request["organization_id"] = org
    if name is not None:
        request["name"] = name
    with client:
        customer = client.customers.create(request=request)
    console.print(f"[bold green]Customer created:[/bold green] {customer.id}")
    render_detail(customer, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_customer(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Customer ID.")],
    email: Annotated[str | None, typer.Option("--email", help="New email.")] = None,
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None,
) -> None:
    """Update a customer."""
    update: dict[str, object] = {}
    if email is not None:
        update["email"] = email
    if name is not None:
        update["name"] = name
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        customer = client.customers.update(id=id, customer_update=update)
    console.print(f"[bold green]Customer updated:[/bold green] {customer.id}")
    render_detail(customer, DETAIL_FIELDS, get_output_format(ctx))


@app.command("delete")
@handle_errors
def delete_customer(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Customer ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a customer."""
    if not yes:
        typer.confirm(f"Delete customer {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.customers.delete(id=id)
    console.print(f"[bold green]Customer deleted:[/bold green] {id}")


@app.command("state")
@handle_errors
def get_state(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Customer ID.")],
) -> None:
    """Get the state (active subscriptions, benefits) for a customer."""
    client = get_client(ctx)
    with client:
        state = client.customers.get_state(id=id)
    render_detail(state, [], get_output_format(ctx))


@app.command("export")
@handle_errors
def export_customers(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
) -> None:
    """Export customers as CSV."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    with client:
        data = client.customers.export(organization_id=org_id)
    output = data.decode("utf-8") if isinstance(data, bytes) else data
    typer.echo(output)
