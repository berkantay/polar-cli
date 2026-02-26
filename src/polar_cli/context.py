"""Typed CLI context — replaces the untyped ctx.obj dict."""

from __future__ import annotations

from dataclasses import dataclass

import typer

from polar_cli.config import Environment, OutputFormat


@dataclass(frozen=True, slots=True)
class CliContext:
    environment: Environment
    output_format: OutputFormat
    base_url: str | None
    verbose: bool
    no_color: bool

    @property
    def sandbox(self) -> bool:
        return self.environment == Environment.SANDBOX


def get_cli_context(ctx: typer.Context) -> CliContext:
    """Extract the typed CliContext from a Typer Context."""
    obj = ctx.obj
    if isinstance(obj, CliContext):
        return obj
    raise RuntimeError("CliContext not initialized — this is a bug.")
