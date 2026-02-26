"""License key commands: list, get, update, validate."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="license-keys", help="Manage license keys.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Key", "key"),
    Column("Status", "status"),
    Column("Usage", "usage"),
    Column("Limit", "limit_usage"),
    Column("Customer ID", "customer_id"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Key", "key"),
    Column("Status", "status"),
    Column("Usage", "usage"),
    Column("Limit", "limit_usage"),
    Column("Validations", "validations"),
    Column("Customer ID", "customer_id"),
    Column("Benefit ID", "benefit_id"),
    Column("Expires At", "expires_at"),
    Column("Created", "created_at"),
]

VALIDATION_FIELDS = [
    Column("ID", "id"),
    Column("Key", "key"),
    Column("Status", "status"),
    Column("Usage", "usage"),
    Column("Limit", "limit_usage"),
    Column("Customer ID", "customer_id"),
    Column("Benefit ID", "benefit_id"),
]


@app.command("list")
@handle_errors
def list_license_keys(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    benefit_id: Annotated[str | None, typer.Option("--benefit-id", help="Filter by benefit.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List license keys."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    kwargs: dict[str, object] = {"organization_id": org_id, "page": page, "limit": limit}
    if benefit_id:
        kwargs["benefit_id"] = benefit_id
    with client:
        res = client.license_keys.list(**kwargs)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get")
@handle_errors
def get_license_key(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="License key ID.")],
) -> None:
    """Get details for a license key (includes activations)."""
    client = get_client(ctx)
    with client:
        lk = client.license_keys.get(id=id)
    render_detail(lk, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_license_key(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="License key ID.")],
    status: Annotated[str | None, typer.Option("--status", help="New status: granted, revoked, disabled.")] = None,
    limit_usage: Annotated[int | None, typer.Option("--limit-usage", help="Set usage limit.")] = None,
) -> None:
    """Update a license key."""
    update: dict[str, object] = {}
    if status is not None:
        update["status"] = status
    if limit_usage is not None:
        update["limit_usage"] = limit_usage
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        lk = client.license_keys.update(id=id, license_key_update=update)
    console.print(f"[bold green]License key updated:[/bold green] {lk.id}")
    render_detail(lk, DETAIL_FIELDS, get_output_format(ctx))


@app.command("validate")
@handle_errors
def validate_license_key(
    ctx: typer.Context,
    key: Annotated[str, typer.Argument(help="The license key string to validate.")],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
) -> None:
    """Validate a license key."""
    client = get_client(ctx)
    request: dict[str, object] = {"key": key}
    if org:
        request["organization_id"] = org
    with client:
        result = client.license_keys.validate(request=request)
    console.print("[bold green]Valid[/bold green]")
    render_detail(result, VALIDATION_FIELDS, get_output_format(ctx))


ACTIVATION_FIELDS = [
    Column("ID", "id"),
    Column("License Key ID", "license_key_id"),
    Column("Label", "label"),
    Column("Created", "created_at"),
]


@app.command("activate")
@handle_errors
def activate_license_key(
    ctx: typer.Context,
    key: Annotated[str, typer.Option("--key", help="The license key string.")],
    label: Annotated[str, typer.Option("--label", help="Activation label (e.g. machine ID).")],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
) -> None:
    """Activate a license key."""
    client = get_client(ctx)
    request: dict[str, object] = {"key": key, "label": label}
    if org:
        request["organization_id"] = org
    with client:
        result = client.license_keys.activate(request=request)
    console.print("[bold green]Activated[/bold green]")
    render_detail(result, ACTIVATION_FIELDS, get_output_format(ctx))


@app.command("deactivate")
@handle_errors
def deactivate_license_key(
    ctx: typer.Context,
    key: Annotated[str, typer.Option("--key", help="The license key string.")],
    activation_id: Annotated[str, typer.Option("--activation-id", help="Activation ID to deactivate.")],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
) -> None:
    """Deactivate a license key activation."""
    client = get_client(ctx)
    request: dict[str, object] = {"key": key, "activation_id": activation_id}
    if org:
        request["organization_id"] = org
    with client:
        client.license_keys.deactivate(request=request)
    console.print("[bold green]Deactivated[/bold green]")


@app.command("get-activation")
@handle_errors
def get_activation(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="License key ID.")],
    activation_id: Annotated[str, typer.Argument(help="Activation ID.")],
) -> None:
    """Get details for a license key activation."""
    client = get_client(ctx)
    with client:
        result = client.license_keys.get_activation(id=id, activation_id=activation_id)
    render_detail(result, ACTIVATION_FIELDS, get_output_format(ctx))
