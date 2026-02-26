"""Table / JSON / YAML rendering with Rich."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, NamedTuple, Protocol, Sequence

import typer
import yaml
from rich.console import Console
from rich.table import Table

from polar_cli.config import OutputFormat

console = Console()


class Column(NamedTuple):
    header: str
    key: str


class HasTotalCount(Protocol):
    total_count: int


def _get_attr(obj: object, key: str) -> object:
    """Get a value from an object by dotted attribute name or dict key."""
    current: object = obj
    for part in key.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


def _format_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, list):
        # Handle lists of enums
        formatted = []
        for v in value:
            if hasattr(v, "value"):
                formatted.append(str(v.value))
            else:
                formatted.append(str(v))
        return ", ".join(formatted)
    # Handle enum values - extract the value instead of showing class name
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _to_dict(obj: object) -> Any:
    """Convert SDK model to a plain dict for serialisation."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")  # type: ignore[union-attr]
    if isinstance(obj, dict):
        return obj
    return {k: v for k, v in vars(obj).items() if not k.startswith("_")}


def render_list(
    items: Sequence[object],
    columns: list[Column],
    pagination: HasTotalCount | None,
    output_format: OutputFormat,
) -> None:
    """Render a list of items in the requested format."""
    if output_format == OutputFormat.JSON:
        data = [_to_dict(item) for item in items]
        console.print_json(json.dumps(data, indent=2, default=str))
        return

    if output_format == OutputFormat.YAML:
        data = [_to_dict(item) for item in items]
        typer.echo(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return

    # Table mode
    table = Table(show_header=True, header_style="bold")
    for col in columns:
        table.add_column(col.header)

    for item in items:
        row = [_format_value(_get_attr(item, col.key)) for col in columns]
        table.add_row(*row)

    console.print(table)

    if pagination is not None:
        console.print(f"[dim]Showing {len(items)} of {pagination.total_count} total[/dim]")


def render_detail(
    obj: object,
    fields: list[Column],
    output_format: OutputFormat,
) -> None:
    """Render a single object in the requested format."""
    if output_format == OutputFormat.JSON:
        console.print_json(json.dumps(_to_dict(obj), indent=2, default=str))
        return

    if output_format == OutputFormat.YAML:
        typer.echo(yaml.dump(_to_dict(obj), default_flow_style=False, sort_keys=False))
        return

    # Table mode (key-value)
    if not fields:
        # No fixed columns defined — fall back to JSON for structured data
        console.print_json(json.dumps(_to_dict(obj), indent=2, default=str))
        return

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="bold")
    table.add_column("Value")

    for field in fields:
        value = _format_value(_get_attr(obj, field.key))
        table.add_row(field.header, value)

    console.print(table)
