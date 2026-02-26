"""Shared fixtures for CLI tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from polar_cli.app import app
from polar_cli.config import OutputFormat
from polar_cli.context import CliContext, Environment


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_app():
    return app


@pytest.fixture
def mock_polar(mocker):
    """Return a mock Polar client and patch get_client to return it."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    mocker.patch("polar_cli.client.get_token", return_value="test-token")
    mocker.patch("polar_cli.client.Polar", return_value=mock_client)
    return mock_client


def make_pagination(total_count: int = 1):
    """Create a mock pagination object."""
    pag = MagicMock()
    pag.total_count = total_count
    return pag


def make_list_result(items: list, total_count: int | None = None):
    """Create a mock list result wrapping items + pagination."""
    result = MagicMock()
    result.result.items = items
    result.result.pagination = make_pagination(total_count if total_count is not None else len(items))
    return result


def make_direct_list_result(items: list, total_count: int | None = None):
    """Create a mock list result with items/pagination at top level (for events API)."""
    result = MagicMock()
    result.items = items
    result.pagination = make_pagination(total_count if total_count is not None else len(items))
    return result
