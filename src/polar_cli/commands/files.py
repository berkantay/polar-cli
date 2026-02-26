"""File commands: list, create, update, delete."""


from typing import Annotated

import typer
from rich.console import Console

from polar_cli.client import get_client
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="files", help="Manage files.")
console = Console()

LIST_COLUMNS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Size", "size"),
    Column("MIME Type", "mime_type"),
    Column("Service", "service"),
    Column("Created", "created_at"),
]

DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("Name", "name"),
    Column("Size", "size"),
    Column("MIME Type", "mime_type"),
    Column("Service", "service"),
    Column("Organization ID", "organization_id"),
    Column("Created", "created_at"),
]


@app.command("list")
@handle_errors
def list_files(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List files."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    with client:
        res = client.files.list(organization_id=org_id, page=page, limit=limit)
    render_list(res.result.items, LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks for S3 multipart upload


def _compute_upload_parts(size: int) -> list[dict[str, object]]:
    """Compute S3 multipart upload parts for a file."""
    parts = []
    chunk_number = 1
    remaining = size
    chunk_start = 0

    while remaining > 0:
        chunk_size = min(CHUNK_SIZE, remaining)
        parts.append({
            "number": chunk_number,
            "chunk_start": chunk_start,
            "chunk_end": chunk_start + chunk_size,
        })
        chunk_number += 1
        chunk_start += chunk_size
        remaining -= chunk_size

    return parts


@app.command("create")
@handle_errors
def create_file(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", help="File name.")],
    mime_type: Annotated[str, typer.Option("--mime-type", help="MIME type (e.g. application/zip).")],
    size: Annotated[int, typer.Option("--size", help="File size in bytes.")],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    service: Annotated[str, typer.Option("--service", help="File service: downloadable, product_media, organization_avatar.")] = "downloadable",
) -> None:
    """Create a file upload entry (returns upload URLs for multipart upload)."""
    parts = _compute_upload_parts(size)
    request: dict[str, object] = {
        "service": service,
        "name": name,
        "mime_type": mime_type,
        "size": size,
        "upload": {"parts": parts},
    }
    if org:
        request["organization_id"] = org
    client = get_client(ctx)
    with client:
        result = client.files.create(request=request)
    console.print(f"[bold green]File entry created:[/bold green] {result.id}")
    console.print(f"[dim]Upload ID: {getattr(result.upload, 'id', 'N/A')}[/dim]")
    console.print(f"[dim]Parts: {len(parts)}[/dim]")
    render_detail(result, DETAIL_FIELDS, get_output_format(ctx))


@app.command("update")
@handle_errors
def update_file(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="File ID.")],
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None,
) -> None:
    """Update a file."""
    update: dict[str, object] = {}
    if name is not None:
        update["name"] = name
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        result = client.files.update(id=id, file_patch=update)
    console.print(f"[bold green]File updated:[/bold green] {result.id}")
    render_detail(result, DETAIL_FIELDS, get_output_format(ctx))


@app.command("delete")
@handle_errors
def delete_file(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="File ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a file."""
    if not yes:
        typer.confirm(f"Delete file {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.files.delete(id=id)
    console.print(f"[bold green]File deleted:[/bold green] {id}")
