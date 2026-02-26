"""Tests for context module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from polar_cli.config import Environment, OutputFormat
from polar_cli.context import CliContext, get_cli_context


class TestCliContext:
    def test_sandbox_property_true(self):
        ctx = CliContext(
            environment=Environment.SANDBOX,
            output_format=OutputFormat.TABLE,
            base_url=None,
            verbose=False,
            no_color=False,
        )
        assert ctx.sandbox is True

    def test_sandbox_property_false(self):
        ctx = CliContext(
            environment=Environment.PRODUCTION,
            output_format=OutputFormat.TABLE,
            base_url=None,
            verbose=False,
            no_color=False,
        )
        assert ctx.sandbox is False

    def test_frozen(self):
        ctx = CliContext(
            environment=Environment.PRODUCTION,
            output_format=OutputFormat.TABLE,
            base_url=None,
            verbose=False,
            no_color=False,
        )
        with pytest.raises(AttributeError):
            ctx.verbose = True  # type: ignore[misc]


class TestGetCliContext:
    def test_valid(self):
        cli_ctx = CliContext(
            environment=Environment.PRODUCTION,
            output_format=OutputFormat.JSON,
            base_url=None,
            verbose=False,
            no_color=False,
        )
        typer_ctx = MagicMock()
        typer_ctx.obj = cli_ctx
        assert get_cli_context(typer_ctx) is cli_ctx

    def test_not_initialized(self):
        typer_ctx = MagicMock()
        typer_ctx.obj = "not a CliContext"
        with pytest.raises(RuntimeError, match="CliContext not initialized"):
            get_cli_context(typer_ctx)

    def test_none_obj(self):
        typer_ctx = MagicMock()
        typer_ctx.obj = None
        with pytest.raises(RuntimeError, match="CliContext not initialized"):
            get_cli_context(typer_ctx)
