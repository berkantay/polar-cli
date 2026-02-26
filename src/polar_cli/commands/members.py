"""Member commands: list, get, create, update, delete."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format

app = typer.Typer(name="members", help="Manage organization members.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Customer ID", "customer_id"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Customer ID", "customer_id"),
    Column("Created", "created_at"),
    Column("Modified", "modified_at"),
]


@app.command("list")
@handle_errors
def list_members(
    ctx: typer.Context,
    customer_id: Annotated[str | None, typer.Option("--customer-id", help="Filter by customer.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List members."""
    client = get_client(ctx)
    kwargs: dict[str, object] = {"page": page, "limit": limit}
    if customer_id:
        kwargs["customer_id"] = customer_id
    with client:
        res = client.members.list_members(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_member(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Member ID.")],
) -> None:
    """Get details for a member."""
    client = get_client(ctx)
    with client:
        member = client.members.get_member(id=id)
    render_detail(member, DETAIL_FIELDS, get_output_format(ctx))


@app.command("create")
@handle_errors
def create_member(
    ctx: typer.Context,
    customer_id: Annotated[str, typer.Option("--customer-id", help="Customer ID.")],
) -> None:
    """Create a member."""
    client = get_client(ctx)
    request: dict[str, object] = {"customer_id": customer_id}
    with client:
        member = client.members.create_member(request=request)
    console.print(f"[bold green]Member created:[/bold green] {member.id}")
    render_detail(member, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_member(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Member ID.")],
    name: Annotated[str | None, typer.Option("--name", help="New member name.")] = None,
    role: Annotated[str | None, typer.Option("--role", help="Member role.")] = None,
) -> None:
    """Update a member."""
    update: dict[str, object] = {}
    if name is not None:
        update["name"] = name
    if role is not None:
        update["role"] = role
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        member = client.members.update_member(id=id, member_update=update)
    console.print(f"[bold green]Member updated:[/bold green] {member.id}")
    render_detail(member, DETAIL_FIELDS, get_output_format(ctx))


@app.command("delete")
@handle_errors
def delete_member(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Member ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a member."""
    if not yes:
        typer.confirm(f"Delete member {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.members.delete_member(id=id)
    console.print(f"[bold green]Member deleted:[/bold green] {id}")
