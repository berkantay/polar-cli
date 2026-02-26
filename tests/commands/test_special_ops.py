"""Tests for special operations: export, state, ingest, names, metrics, etc.

Covers: customers export/state, events ingest/names, metrics get/limits,
orders export/generate-invoice/update, subscriptions create/export.
"""

from unittest.mock import MagicMock

from tests.conftest import make_direct_list_result, make_list_result


# --- customers: export, state ---


class TestCustomersExport:
    def test_export(self, runner, cli_app, mock_polar, mocker):
        mock_polar.customers.export.return_value = b"id,email\n1,a@b.com\n"
        mocker.patch("polar_cli.commands.customers.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["customers", "export"])
        assert result.exit_code == 0


class TestCustomersState:
    def test_state(self, runner, cli_app, mock_polar):
        state = MagicMock()
        state.model_dump.return_value = {"subscriptions": [], "benefits": []}
        mock_polar.customers.get_state.return_value = state
        result = runner.invoke(cli_app, ["customers", "state", "cust-1"])
        assert result.exit_code == 0


# --- events: ingest, names ---


class TestEventsIngest:
    def test_ingest(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, [
            "events", "ingest",
            '[{"name": "page.view", "external_customer_id": "c-1"}]',
        ])
        assert result.exit_code == 0
        assert "Ingested 1 event(s)" in result.output
        mock_polar.events.ingest.assert_called_once()

    def test_ingest_multiple(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, [
            "events", "ingest",
            '[{"name": "a"}, {"name": "b"}, {"name": "c"}]',
        ])
        assert result.exit_code == 0
        assert "Ingested 3 event(s)" in result.output


class TestEventsNames:
    def test_names(self, runner, cli_app, mock_polar, mocker):
        n = MagicMock()
        n.name = "page.view"
        n.source = "api"
        mock_polar.events.list_names.return_value = make_direct_list_result([n])
        mocker.patch("polar_cli.commands.events.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["events", "names"])
        assert result.exit_code == 0


# --- metrics: get, limits ---


class TestMetricsGet:
    def test_get(self, runner, cli_app, mock_polar, mocker):
        m = MagicMock()
        m.model_dump.return_value = {"revenue": [100, 200], "periods": ["2024-01", "2024-02"]}
        mock_polar.metrics.get.return_value = m
        mocker.patch("polar_cli.commands.metrics.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, [
            "metrics", "get",
            "--start-date", "2024-01-01", "--end-date", "2024-03-01",
        ])
        assert result.exit_code == 0

    def test_get_with_product_filter(self, runner, cli_app, mock_polar, mocker):
        m = MagicMock()
        m.model_dump.return_value = {}
        mock_polar.metrics.get.return_value = m
        mocker.patch("polar_cli.commands.metrics.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, [
            "metrics", "get",
            "--start-date", "2024-01-01", "--end-date", "2024-03-01",
            "--product-id", "prod-1",
        ])
        assert result.exit_code == 0
        call_kwargs = mock_polar.metrics.get.call_args[1]
        assert call_kwargs["product_id"] == "prod-1"


class TestMetricsLimits:
    def test_limits(self, runner, cli_app, mock_polar):
        limits = MagicMock()
        limits.model_dump.return_value = {"min_date": "2023-01-01"}
        mock_polar.metrics.limits.return_value = limits
        result = runner.invoke(cli_app, ["metrics", "limits"])
        assert result.exit_code == 0


# --- orders: export, generate-invoice, update ---


class TestOrdersExport:
    def test_export(self, runner, cli_app, mock_polar, mocker):
        mock_polar.orders.export.return_value = b"id,amount\n1,1000\n"
        mocker.patch("polar_cli.commands.orders.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["orders", "export"])
        assert result.exit_code == 0


class TestOrdersGenerateInvoice:
    def test_generate(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["orders", "generate-invoice", "ord-1"])
        assert result.exit_code == 0
        assert "Invoice generated" in result.output
        mock_polar.orders.generate_invoice.assert_called_once()


class TestOrdersUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        order = MagicMock(id="ord-1")
        mock_polar.orders.update.return_value = order
        result = runner.invoke(cli_app, ["orders", "update", "ord-1", "--billing-name", "Jane Doe"])
        assert result.exit_code == 0
        assert "Order updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["orders", "update", "ord-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


# --- subscriptions: create, export ---


class TestSubscriptionsCreate:
    def test_create(self, runner, cli_app, mock_polar):
        sub = MagicMock(id="sub-new")
        mock_polar.subscriptions.create.return_value = sub
        result = runner.invoke(cli_app, [
            "subscriptions", "create",
            "--product-id", "prod-1", "--customer-id", "cust-1",
        ])
        assert result.exit_code == 0
        assert "Subscription created" in result.output


class TestSubscriptionsExport:
    def test_export(self, runner, cli_app, mock_polar, mocker):
        mock_polar.subscriptions.export.return_value = b"id,status\n1,active\n"
        mocker.patch("polar_cli.commands.subscriptions.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["subscriptions", "export"])
        assert result.exit_code == 0
