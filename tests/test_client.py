"""Tests for client module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import typer

from polar_cli.client import SERVER_URLS, get_base_url, get_client, require_token
from polar_cli.config import Environment, OutputFormat
from polar_cli.context import CliContext


def _make_ctx(
    env: Environment = Environment.PRODUCTION,
    base_url: str | None = None,
) -> MagicMock:
    ctx = MagicMock(spec=typer.Context)
    ctx.obj = CliContext(
        environment=env,
        output_format=OutputFormat.TABLE,
        base_url=base_url,
        verbose=False,
        no_color=False,
    )
    return ctx


class TestGetClient:
    def test_production(self, mocker):
        mocker.patch("polar_cli.client.get_token", return_value="tok")
        mock_polar = mocker.patch("polar_cli.client.Polar")
        ctx = _make_ctx(Environment.PRODUCTION)

        get_client(ctx)
        mock_polar.assert_called_once_with(access_token="tok", server="production")

    def test_sandbox(self, mocker):
        mocker.patch("polar_cli.client.get_token", return_value="tok")
        mock_polar = mocker.patch("polar_cli.client.Polar")
        ctx = _make_ctx(Environment.SANDBOX)

        get_client(ctx)
        mock_polar.assert_called_once_with(access_token="tok", server="sandbox")

    def test_custom_base_url(self, mocker):
        mocker.patch("polar_cli.client.get_token", return_value="tok")
        mock_polar = mocker.patch("polar_cli.client.Polar")
        ctx = _make_ctx(base_url="https://custom.polar.sh")

        get_client(ctx)
        mock_polar.assert_called_once_with(access_token="tok", server_url="https://custom.polar.sh")

    def test_no_token_exits(self, mocker):
        mocker.patch("polar_cli.client.get_token", return_value=None)
        ctx = _make_ctx()

        with pytest.raises(typer.Exit):
            get_client(ctx)


class TestGetBaseUrl:
    def test_production(self):
        ctx = _make_ctx(Environment.PRODUCTION)
        assert get_base_url(ctx) == "https://api.polar.sh"

    def test_sandbox(self):
        ctx = _make_ctx(Environment.SANDBOX)
        assert get_base_url(ctx) == "https://sandbox-api.polar.sh"

    def test_custom_base_url_strips_trailing_slash(self):
        ctx = _make_ctx(base_url="https://custom.polar.sh/")
        assert get_base_url(ctx) == "https://custom.polar.sh"


class TestRequireToken:
    def test_returns_token(self, mocker):
        mocker.patch("polar_cli.client.get_token", return_value="my-token")
        ctx = _make_ctx()
        assert require_token(ctx) == "my-token"

    def test_exits_when_no_token(self, mocker):
        mocker.patch("polar_cli.client.get_token", return_value=None)
        ctx = _make_ctx()
        with pytest.raises(typer.Exit):
            require_token(ctx)

    def test_exits_sandbox_message(self, mocker, capsys):
        mocker.patch("polar_cli.client.get_token", return_value=None)
        ctx = _make_ctx(Environment.SANDBOX)
        with pytest.raises(typer.Exit):
            require_token(ctx)
