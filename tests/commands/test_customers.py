"""Tests for customers commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from tests.conftest import make_list_result


class TestCustomersList:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        customer = MagicMock()
        customer.id = "cust-1"
        customer.email = "alice@example.com"
        customer.name = "Alice"
        customer.created_at = "2024-01-01"

        mock_polar.customers.list.return_value = make_list_result([customer])
        mocker.patch("polar_cli.commands.customers.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["customers", "list"])
        assert result.exit_code == 0
        assert "alice@example.com" in result.output


class TestCustomersGet:
    def test_get(self, runner, cli_app, mock_polar):
        customer = MagicMock()
        customer.id = "cust-1"
        customer.email = "alice@example.com"
        customer.name = "Alice"
        customer.organization_id = "org-1"
        customer.created_at = "2024-01-01"

        mock_polar.customers.get.return_value = customer

        result = runner.invoke(cli_app, ["customers", "get", "cust-1"])
        assert result.exit_code == 0
        assert "Alice" in result.output


class TestCustomersCreate:
    def test_create(self, runner, cli_app, mock_polar, mocker):
        customer = MagicMock()
        customer.id = "cust-new"
        customer.email = "bob@example.com"
        customer.name = "Bob"
        customer.organization_id = "org-1"
        customer.created_at = "2024-01-01"

        mock_polar.customers.create.return_value = customer
        mocker.patch("polar_cli.commands.customers.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["customers", "create", "--email", "bob@example.com"])
        assert result.exit_code == 0
        assert "Customer created" in result.output
