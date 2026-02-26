"""Tests for subscriptions commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from tests.conftest import make_list_result


class TestSubscriptionsList:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        sub = MagicMock()
        sub.id = "sub-1"
        sub.product_id = "prod-1"
        sub.customer_id = "cust-1"
        sub.status = "active"
        sub.current_period_start = "2024-01-01"
        sub.current_period_end = "2024-02-01"

        mock_polar.subscriptions.list.return_value = make_list_result([sub])
        mocker.patch("polar_cli.commands.subscriptions.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["subscriptions", "list"])
        assert result.exit_code == 0
        assert "sub-1" in result.output


class TestSubscriptionsGet:
    def test_get(self, runner, cli_app, mock_polar):
        sub = MagicMock()
        sub.id = "sub-1"
        sub.product_id = "prod-1"
        sub.customer_id = "cust-1"
        sub.status = "active"
        sub.current_period_start = "2024-01-01"
        sub.current_period_end = "2024-02-01"
        sub.cancel_at_period_end = False
        sub.created_at = "2024-01-01"

        mock_polar.subscriptions.get.return_value = sub

        result = runner.invoke(cli_app, ["subscriptions", "get", "sub-1"])
        assert result.exit_code == 0
        assert "sub-1" in result.output
