"""Tests for orders commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from tests.conftest import make_list_result


class TestOrdersList:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        order = MagicMock()
        order.id = "ord-1"
        order.product_id = "prod-1"
        order.customer_id = "cust-1"
        order.amount = 1000
        order.currency = "usd"
        order.created_at = "2024-01-01"

        mock_polar.orders.list.return_value = make_list_result([order])
        mocker.patch("polar_cli.commands.orders.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["orders", "list"])
        assert result.exit_code == 0
        assert "ord-1" in result.output


class TestOrdersGet:
    def test_get(self, runner, cli_app, mock_polar):
        order = MagicMock()
        order.id = "ord-1"
        order.product_id = "prod-1"
        order.customer_id = "cust-1"
        order.amount = 1000
        order.currency = "usd"
        order.tax_amount = 100
        order.created_at = "2024-01-01"

        mock_polar.orders.get.return_value = order

        result = runner.invoke(cli_app, ["orders", "get", "ord-1"])
        assert result.exit_code == 0
        assert "ord-1" in result.output
