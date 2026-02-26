"""Webhook commands: listen (SSE), endpoint CRUD, deliveries."""


import json
from typing import Annotated

import httpx
import typer
from httpx_sse import connect_sse
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from polar_cli.client import get_base_url, get_client, require_token
from polar_cli.errors import handle_errors
from polar_cli.output import Column, render_detail, render_list
from polar_cli.utils import get_output_format, resolve_org_id

app = typer.Typer(name="webhooks", help="Webhook listener and management.")
console = Console()

ENDPOINT_LIST_COLUMNS = [
    Column("ID", "id"),
    Column("URL", "url"),
    Column("Created", "created_at"),
]

ENDPOINT_DETAIL_FIELDS = [
    Column("ID", "id"),
    Column("URL", "url"),
    Column("Secret", "secret"),
    Column("Events", "events"),
    Column("Created", "created_at"),
]

DELIVERY_COLUMNS = [
    Column("ID", "id"),
    Column("Event Type", "event_type"),
    Column("HTTP Code", "http_code"),
    Column("Succeeded", "succeeded"),
    Column("Created", "created_at"),
]


# --- SSE listener ---


@app.command("listen")
@handle_errors
def listen(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    forward_to: Annotated[
        str | None,
        typer.Option("--forward-to", "-f", help="Local URL to forward webhook payloads to."),
    ] = None,
) -> None:
    """Listen for webhook events in real-time via SSE."""
    org_id = resolve_org_id(ctx, org)
    token = require_token(ctx)
    base = get_base_url(ctx)
    sse_url = f"{base}/v1/cli/listen/{org_id}"

    console.print("[bold]Connecting to event stream...[/bold]")
    console.print(f"[dim]URL: {sse_url}[/dim]")
    if forward_to:
        console.print(f"[dim]Forwarding to: {forward_to}[/dim]")

    headers = {"Authorization": f"Bearer {token}"}

    with httpx.Client(timeout=None) as http_client:
        with connect_sse(http_client, "GET", sse_url, headers=headers) as event_source:
            if event_source.response.status_code != 200:
                console.print(f"[bold red]Failed to connect:[/bold red] HTTP {event_source.response.status_code}")
                raise typer.Exit(1)

            for sse in event_source.iter_sse():
                if not sse.data:
                    continue
                try:
                    event: dict[str, object] = json.loads(sse.data)
                except json.JSONDecodeError:
                    continue

                key = str(event.get("key", "unknown"))

                if key == "connected":
                    console.print("[bold green]Connected![/bold green] Listening for events...")
                    console.print(f"[dim]Signing secret: {event.get('secret', '')}[/dim]\n")
                    continue

                _display_event(event, key)

                if forward_to and key == "webhook.created":
                    _forward_event(http_client, forward_to, event)


def _display_event(event: dict[str, object], key: str) -> None:
    payload = event.get("payload", {})
    event_headers = event.get("headers", {})
    ts = event.get("ts", "")

    syntax = Syntax(json.dumps(payload, indent=2, default=str), "json", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=f"[bold]{key}[/bold] [dim]{ts}[/dim]", border_style="blue"))

    if isinstance(event_headers, dict) and event_headers:
        header_lines = "\n".join(f"  {k}: {v}" for k, v in event_headers.items())
        console.print(f"[dim]Headers:\n{header_lines}[/dim]")
    console.print()


def _forward_event(http_client: httpx.Client, url: str, event: dict[str, object]) -> None:
    payload = event.get("payload", {})
    event_headers = event.get("headers", {})
    if not isinstance(payload, dict) or not isinstance(event_headers, dict):
        return

    webhook_payload = payload.get("payload", payload)
    body = json.dumps(webhook_payload, default=str)
    forward_headers = dict(event_headers)
    forward_headers["content-type"] = "application/json"

    try:
        resp = http_client.post(url, content=body, headers=forward_headers, timeout=10)
        style = "green" if resp.status_code < 400 else "red"
        console.print(f"  [dim]Forwarded →[/dim] [{style}]{resp.status_code}[/{style}] {url}")
    except httpx.RequestError as exc:
        console.print(f"  [bold red]Forward failed:[/bold red] {exc}")


# --- Endpoint CRUD ---


@app.command("endpoints")
@handle_errors
def list_endpoints(
    ctx: typer.Context,
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List webhook endpoints."""
    org_id = resolve_org_id(ctx, org)
    client = get_client(ctx)
    with client:
        res = client.webhooks.list_webhook_endpoints(organization_id=org_id, page=page, limit=limit)
    render_list(res.result.items, ENDPOINT_LIST_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("get-endpoint")
@handle_errors
def get_endpoint(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Webhook endpoint ID.")],
) -> None:
    """Get details for a webhook endpoint."""
    client = get_client(ctx)
    with client:
        endpoint = client.webhooks.get_webhook_endpoint(id=id)
    render_detail(endpoint, ENDPOINT_DETAIL_FIELDS, get_output_format(ctx))


@app.command("create-endpoint")
@handle_errors
def create_endpoint(
    ctx: typer.Context,
    url: Annotated[str, typer.Option("--url", help="Endpoint URL.")],
    org: Annotated[str | None, typer.Option("--org", help="Organization ID.")] = None,
    events: Annotated[list[str] | None, typer.Option("--event", help="Event types to subscribe to (repeat for multiple).")] = None,
    format: Annotated[str, typer.Option("--format", help="Payload format: raw or discord.")] = "raw",
) -> None:
    """Create a webhook endpoint."""
    request: dict[str, object] = {"url": url, "format": format}
    if org:
        request["organization_id"] = org
    if events:
        request["events"] = events
    client = get_client(ctx)
    with client:
        endpoint = client.webhooks.create_webhook_endpoint(request=request)
    console.print(f"[bold green]Endpoint created:[/bold green] {endpoint.id}")
    render_detail(endpoint, ENDPOINT_DETAIL_FIELDS, get_output_format(ctx))


@app.command("update-endpoint")
@handle_errors
def update_endpoint(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Webhook endpoint ID.")],
    url: Annotated[str | None, typer.Option("--url", help="New URL.")] = None,
    events: Annotated[list[str] | None, typer.Option("--event", help="Event types (repeat for multiple).")] = None,
) -> None:
    """Update a webhook endpoint."""
    update: dict[str, object] = {}
    if url is not None:
        update["url"] = url
    if events is not None:
        update["events"] = events
    if not update:
        console.print("[dim]Nothing to update.[/dim]")
        raise typer.Exit()
    client = get_client(ctx)
    with client:
        endpoint = client.webhooks.update_webhook_endpoint(id=id, webhook_endpoint_update=update)
    console.print(f"[bold green]Endpoint updated:[/bold green] {endpoint.id}")
    render_detail(endpoint, ENDPOINT_DETAIL_FIELDS, get_output_format(ctx))


@app.command("delete-endpoint")
@handle_errors
def delete_endpoint(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Webhook endpoint ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a webhook endpoint."""
    if not yes:
        typer.confirm(f"Delete webhook endpoint {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.webhooks.delete_webhook_endpoint(id=id)
    console.print(f"[bold green]Endpoint deleted:[/bold green] {id}")


# --- Deliveries ---


@app.command("deliveries")
@handle_errors
def list_deliveries(
    ctx: typer.Context,
    endpoint_id: Annotated[str | None, typer.Option("--endpoint-id", help="Filter by endpoint.")] = None,
    succeeded: Annotated[bool | None, typer.Option("--succeeded/--failed", help="Filter by delivery status.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    limit: Annotated[int, typer.Option(help="Items per page.")] = 20,
) -> None:
    """List webhook deliveries."""
    client = get_client(ctx)
    kwargs: dict[str, object] = {"page": page, "limit": limit}
    if endpoint_id:
        kwargs["endpoint_id"] = endpoint_id
    if succeeded is not None:
        kwargs["succeeded"] = succeeded
    with client:
        res = client.webhooks.list_webhook_deliveries(**kwargs)
    render_list(res.result.items, DELIVERY_COLUMNS, res.result.pagination, get_output_format(ctx))


@app.command("redeliver")
@handle_errors
def redeliver(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Webhook event ID to redeliver.")],
) -> None:
    """Redeliver a webhook event."""
    client = get_client(ctx)
    with client:
        client.webhooks.redeliver_webhook_event(id=id)
    console.print(f"[bold green]Event redelivered:[/bold green] {id}")


@app.command("reset-secret")
@handle_errors
def reset_secret(
    ctx: typer.Context,
    id: Annotated[str, typer.Argument(help="Webhook endpoint ID.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Reset the signing secret for a webhook endpoint."""
    if not yes:
        typer.confirm(f"Reset secret for endpoint {id}?", abort=True)
    client = get_client(ctx)
    with client:
        client.webhooks.reset_webhook_endpoint_secret(id=id)
    console.print(f"[bold green]Secret reset for endpoint:[/bold green] {id}")
