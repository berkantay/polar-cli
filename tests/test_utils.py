"""Tests for utils module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import typer

from polar_cli.config import Environment, OutputFormat
from polar_cli.context import CliContext
from polar_cli.utils import get_output_format, resolve_org_id


def _make_ctx(
    env: Environment = Environment.PRODUCTION,
    output: OutputFormat = OutputFormat.TABLE,
) -> MagicMock:
    ctx = MagicMock(spec=typer.Context)
    ctx.obj = CliContext(
        environment=env,
        output_format=output,
        base_url=None,
        verbose=False,
        no_color=False,
    )
    return ctx


class TestResolveOrgId:
    def test_flag_takes_priority(self):
        ctx = _make_ctx()
        assert resolve_org_id(ctx, "org-from-flag") == "org-from-flag"

    def test_falls_back_to_default(self, mocker):
        mocker.patch("polar_cli.utils.get_default_org_id", return_value="org-default")
        ctx = _make_ctx()
        assert resolve_org_id(ctx, None) == "org-default"

    def test_exits_when_no_org(self, mocker):
        mocker.patch("polar_cli.utils.get_default_org_id", return_value=None)
        ctx = _make_ctx()
        with pytest.raises(typer.Exit):
            resolve_org_id(ctx, None)

    def test_flag_none_but_default_exists(self, mocker):
        mocker.patch("polar_cli.utils.get_default_org_id", return_value="saved-org")
        ctx = _make_ctx(Environment.SANDBOX)
        result = resolve_org_id(ctx, None)
        assert result == "saved-org"


class TestGetOutputFormat:
    def test_table(self):
        ctx = _make_ctx(output=OutputFormat.TABLE)
        assert get_output_format(ctx) == OutputFormat.TABLE

    def test_json(self):
        ctx = _make_ctx(output=OutputFormat.JSON)
        assert get_output_format(ctx) == OutputFormat.JSON

    def test_yaml(self):
        ctx = _make_ctx(output=OutputFormat.YAML)
        assert get_output_format(ctx) == OutputFormat.YAML
