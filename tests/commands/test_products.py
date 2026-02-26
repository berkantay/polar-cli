"""Tests for products commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from tests.conftest import make_list_result


class TestProductsList:
    def test_list_table(self, runner, cli_app, mock_polar, mocker):
        product = MagicMock()
        product.id = "prod-1"
        product.name = "Test Product"
        product.is_archived = False
        product.created_at = "2024-01-01"

        mock_polar.products.list.return_value = make_list_result([product])
        mocker.patch("polar_cli.commands.products.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["products", "list"])
        assert result.exit_code == 0
        assert "Test Product" in result.output

    def test_list_json(self, runner, cli_app, mock_polar, mocker):
        product = MagicMock()
        product.id = "prod-1"
        product.name = "JSON Product"
        product.model_dump.return_value = {"id": "prod-1", "name": "JSON Product"}

        mock_polar.products.list.return_value = make_list_result([product])
        mocker.patch("polar_cli.commands.products.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["--output", "json", "products", "list"])
        assert result.exit_code == 0
        assert "prod-1" in result.output


class TestProductsGet:
    def test_get(self, runner, cli_app, mock_polar):
        product = MagicMock()
        product.id = "prod-1"
        product.name = "My Product"
        product.description = "A product"
        product.is_archived = False
        product.organization_id = "org-1"
        product.created_at = "2024-01-01"
        product.modified_at = None

        mock_polar.products.get.return_value = product

        result = runner.invoke(cli_app, ["products", "get", "prod-1"])
        assert result.exit_code == 0
        assert "My Product" in result.output


class TestProductsCreate:
    def test_create(self, runner, cli_app, mock_polar, mocker):
        product = MagicMock()
        product.id = "prod-new"
        product.name = "New Product"
        product.description = None
        product.is_archived = False
        product.organization_id = "org-1"
        product.created_at = "2024-01-01"
        product.modified_at = None

        mock_polar.products.create.return_value = product
        mocker.patch("polar_cli.commands.products.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["products", "create", "--name", "New Product"])
        assert result.exit_code == 0
        assert "Product created" in result.output


class TestProductsUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        product = MagicMock()
        product.id = "prod-1"
        product.name = "Updated"
        product.description = None
        product.is_archived = False
        product.organization_id = "org-1"
        product.created_at = "2024-01-01"
        product.modified_at = "2024-02-01"

        mock_polar.products.update.return_value = product

        result = runner.invoke(cli_app, ["products", "update", "prod-1", "--name", "Updated"])
        assert result.exit_code == 0
        assert "Product updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["products", "update", "prod-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output

    def test_update_archive(self, runner, cli_app, mock_polar):
        product = MagicMock(id="prod-1")
        mock_polar.products.update.return_value = product

        result = runner.invoke(cli_app, ["products", "update", "prod-1", "--is-archived"])
        assert result.exit_code == 0
        assert "Product updated" in result.output
        call_kwargs = mock_polar.products.update.call_args[1]
        assert call_kwargs["product_update"]["is_archived"] is True

    def test_update_description(self, runner, cli_app, mock_polar):
        product = MagicMock(id="prod-1")
        mock_polar.products.update.return_value = product

        result = runner.invoke(cli_app, ["products", "update", "prod-1", "--description", "New desc"])
        assert result.exit_code == 0
        call_kwargs = mock_polar.products.update.call_args[1]
        assert call_kwargs["product_update"]["description"] == "New desc"


class TestProductsCreateWithPrice:
    def test_create_with_one_time_price(self, runner, cli_app, mock_polar, mocker):
        product = MagicMock(id="prod-priced")
        mock_polar.products.create.return_value = product
        mocker.patch("polar_cli.commands.products.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, [
            "products", "create", "--name", "Priced", "--price-amount", "999",
        ])
        assert result.exit_code == 0
        call_kwargs = mock_polar.products.create.call_args[1]
        prices = call_kwargs["request"]["prices"]
        assert len(prices) == 1
        assert prices[0]["type"] == "one_time"
        assert prices[0]["price_amount"] == 999

    def test_create_with_recurring_price(self, runner, cli_app, mock_polar, mocker):
        product = MagicMock(id="prod-sub")
        mock_polar.products.create.return_value = product
        mocker.patch("polar_cli.commands.products.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, [
            "products", "create", "--name", "Sub",
            "--price-amount", "1999", "--recurring-interval", "month",
        ])
        assert result.exit_code == 0
        call_kwargs = mock_polar.products.create.call_args[1]
        prices = call_kwargs["request"]["prices"]
        assert prices[0]["type"] == "recurring"
        assert prices[0]["recurring_interval"] == "month"

    def test_create_with_query_filter(self, runner, cli_app, mock_polar, mocker):
        product = MagicMock(id="prod-1", name="Matching")
        mock_polar.products.list.return_value = make_list_result([product])
        mocker.patch("polar_cli.commands.products.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["products", "list", "--query", "Match"])
        assert result.exit_code == 0
        call_kwargs = mock_polar.products.list.call_args[1]
        assert call_kwargs["query"] == "Match"


class TestProductsListYaml:
    def test_list_yaml(self, runner, cli_app, mock_polar, mocker):
        product = MagicMock()
        product.model_dump.return_value = {"id": "prod-1", "name": "YAML Product"}
        mock_polar.products.list.return_value = make_list_result([product])
        mocker.patch("polar_cli.commands.products.resolve_org_id", return_value="org-1")

        result = runner.invoke(cli_app, ["--output", "yaml", "products", "list"])
        assert result.exit_code == 0
        assert "id:" in result.output
