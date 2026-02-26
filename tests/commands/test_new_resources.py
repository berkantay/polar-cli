"""Tests for all new/expanded resource commands.

Each resource gets a list + get test (the common pattern), plus tests for
any non-standard operations (create, delete, revoke, invoice, validate, etc.).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from tests.conftest import make_direct_list_result, make_list_result


# --- Customers: update, delete ---


class TestCustomersUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        customer = MagicMock(id="cust-1", email="new@example.com", name="New", organization_id="org-1", created_at="2024-01-01")
        mock_polar.customers.update.return_value = customer
        result = runner.invoke(cli_app, ["customers", "update", "cust-1", "--email", "new@example.com"])
        assert result.exit_code == 0
        assert "Customer updated" in result.output


class TestCustomersDelete:
    def test_delete(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["customers", "delete", "cust-1", "--yes"])
        assert result.exit_code == 0
        assert "Customer deleted" in result.output
        mock_polar.customers.delete.assert_called_once()


# --- Subscriptions: update, revoke ---


class TestSubscriptionsUpdate:
    def test_cancel_at_period_end(self, runner, cli_app, mock_polar):
        sub = MagicMock(id="sub-1")
        mock_polar.subscriptions.update.return_value = sub
        result = runner.invoke(cli_app, ["subscriptions", "update", "sub-1", "--cancel-at-period-end"])
        assert result.exit_code == 0
        assert "Subscription updated" in result.output


class TestSubscriptionsRevoke:
    def test_revoke(self, runner, cli_app, mock_polar):
        sub = MagicMock(id="sub-1")
        mock_polar.subscriptions.revoke.return_value = sub
        result = runner.invoke(cli_app, ["subscriptions", "revoke", "sub-1", "--yes"])
        assert result.exit_code == 0
        assert "Subscription revoked" in result.output


# --- Orders: invoice ---


class TestOrdersInvoice:
    def test_invoice(self, runner, cli_app, mock_polar):
        invoice = MagicMock(url="https://polar.sh/invoice/123")
        mock_polar.orders.invoice.return_value = invoice
        result = runner.invoke(cli_app, ["orders", "invoice", "ord-1"])
        assert result.exit_code == 0
        assert "https://polar.sh/invoice/123" in result.output


# --- Webhooks: endpoints CRUD, deliveries, redeliver ---


class TestWebhookEndpoints:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        ep = MagicMock(id="ep-1", url="https://example.com/hook", created_at="2024-01-01")
        mock_polar.webhooks.list_webhook_endpoints.return_value = make_list_result([ep])
        mocker.patch("polar_cli.commands.webhooks.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["webhooks", "endpoints"])
        assert result.exit_code == 0
        assert "ep-1" in result.output

    def test_create(self, runner, cli_app, mock_polar, mocker):
        ep = MagicMock(id="ep-new", url="https://example.com/hook", secret="sec", events=[], created_at="2024-01-01")
        mock_polar.webhooks.create_webhook_endpoint.return_value = ep
        mocker.patch("polar_cli.commands.webhooks.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["webhooks", "create-endpoint", "--url", "https://example.com/hook"])
        assert result.exit_code == 0
        assert "Endpoint created" in result.output

    def test_delete(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["webhooks", "delete-endpoint", "ep-1", "--yes"])
        assert result.exit_code == 0
        assert "Endpoint deleted" in result.output


class TestWebhookDeliveries:
    def test_list(self, runner, cli_app, mock_polar):
        delivery = MagicMock(id="del-1", event_type="order.created", http_code=200, succeeded=True, created_at="2024-01-01")
        mock_polar.webhooks.list_webhook_deliveries.return_value = make_list_result([delivery])
        result = runner.invoke(cli_app, ["webhooks", "deliveries"])
        assert result.exit_code == 0
        assert "del-1" in result.output


class TestWebhookRedeliver:
    def test_redeliver(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["webhooks", "redeliver", "evt-1"])
        assert result.exit_code == 0
        assert "Event redelivered" in result.output


# --- Checkout links ---


class TestCheckoutLinks:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        link = MagicMock(id="cl-1", product_id="p-1", url="https://polar.sh/checkout/cl-1", created_at="2024-01-01")
        mock_polar.checkout_links.list.return_value = make_list_result([link])
        mocker.patch("polar_cli.commands.checkout_links.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["checkout-links", "list"])
        assert result.exit_code == 0
        assert "cl-1" in result.output

    def test_create(self, runner, cli_app, mock_polar):
        link = MagicMock(id="cl-new", url="https://polar.sh/checkout/cl-new")
        mock_polar.checkout_links.create.return_value = link
        result = runner.invoke(cli_app, ["checkout-links", "create", "--product-id", "p-1"])
        assert result.exit_code == 0
        assert "Checkout link created" in result.output

    def test_delete(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["checkout-links", "delete", "cl-1", "--yes"])
        assert result.exit_code == 0
        assert "Checkout link deleted" in result.output


# --- Checkouts ---


class TestCheckouts:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        co = MagicMock(id="co-1", product_id="p-1", status="open", amount=1000, currency="usd", created_at="2024-01-01")
        mock_polar.checkouts.list.return_value = make_list_result([co])
        mocker.patch("polar_cli.commands.checkouts.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["checkouts", "list"])
        assert result.exit_code == 0
        assert "co-1" in result.output

    def test_create(self, runner, cli_app, mock_polar):
        co = MagicMock(id="co-new", url="https://polar.sh/checkout/co-new")
        mock_polar.checkouts.create.return_value = co
        result = runner.invoke(cli_app, ["checkouts", "create", "--product", "p-1"])
        assert result.exit_code == 0
        assert "Checkout created" in result.output


# --- Discounts ---


class TestDiscounts:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        d = MagicMock(id="disc-1", name="10OFF", code="10OFF", type="percentage", amount=10, created_at="2024-01-01")
        mock_polar.discounts.list.return_value = make_list_result([d])
        mocker.patch("polar_cli.commands.discounts.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["discounts", "list"])
        assert result.exit_code == 0
        assert "disc-1" in result.output

    def test_create(self, runner, cli_app, mock_polar, mocker):
        d = MagicMock(id="disc-new")
        mock_polar.discounts.create.return_value = d
        mocker.patch("polar_cli.commands.discounts.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["discounts", "create", "--name", "Half Off", "--type", "percentage", "--amount", "50"])
        assert result.exit_code == 0
        assert "Discount created" in result.output

    def test_delete(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["discounts", "delete", "disc-1", "--yes"])
        assert result.exit_code == 0
        assert "Discount deleted" in result.output


# --- Benefits ---


class TestBenefits:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        b = MagicMock(id="ben-1", type="custom", description="Early access", selectable=True, created_at="2024-01-01")
        mock_polar.benefits.list.return_value = make_list_result([b])
        mocker.patch("polar_cli.commands.benefits.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["benefits", "list"])
        assert result.exit_code == 0
        assert "ben-1" in result.output

    def test_delete(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["benefits", "delete", "ben-1", "--yes"])
        assert result.exit_code == 0
        assert "Benefit deleted" in result.output


# --- License keys ---


class TestLicenseKeys:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        lk = MagicMock(id="lk-1", key="AAAA-BBBB", status="granted", usage=0, limit_usage=10, customer_id="c-1")
        mock_polar.license_keys.list.return_value = make_list_result([lk])
        mocker.patch("polar_cli.commands.license_keys.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["license-keys", "list"])
        assert result.exit_code == 0
        assert "lk-1" in result.output

    def test_validate(self, runner, cli_app, mock_polar, mocker):
        validated = MagicMock(id="lk-1", key="AAAA-BBBB", status="granted", usage=1, limit_usage=10, customer_id="c-1", benefit_id="b-1")
        mock_polar.license_keys.validate.return_value = validated
        mocker.patch("polar_cli.commands.license_keys.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["license-keys", "validate", "AAAA-BBBB"])
        assert result.exit_code == 0
        assert "Valid" in result.output


# --- Meters ---


class TestMeters:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        m = MagicMock(id="m-1", name="API calls", filter="{}", aggregation="{}", created_at="2024-01-01")
        mock_polar.meters.list.return_value = make_list_result([m])
        mocker.patch("polar_cli.commands.meters.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["meters", "list"])
        assert result.exit_code == 0
        assert "m-1" in result.output


# --- Events ---


class TestEvents:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        e = MagicMock(id="evt-1", name="page.view", source="api", customer_id="c-1", created_at="2024-01-01")
        mock_polar.events.list.return_value = make_direct_list_result([e])
        mocker.patch("polar_cli.commands.events.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["events", "list"])
        assert result.exit_code == 0
        assert "evt-1" in result.output

    def test_get(self, runner, cli_app, mock_polar):
        e = MagicMock(id="evt-1", name="page.view")
        mock_polar.events.get.return_value = e
        result = runner.invoke(cli_app, ["events", "get", "evt-1"])
        assert result.exit_code == 0
        assert "evt-1" in result.output


# --- Refunds ---


class TestRefunds:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        r = MagicMock(id="ref-1", order_id="ord-1", amount=500, currency="usd", reason="customer_request", succeeded=True, created_at="2024-01-01")
        mock_polar.refunds.list.return_value = make_list_result([r])
        mocker.patch("polar_cli.commands.refunds.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["refunds", "list"])
        assert result.exit_code == 0
        assert "ref-1" in result.output

    def test_create(self, runner, cli_app, mock_polar):
        r = MagicMock(id="ref-new")
        mock_polar.refunds.create.return_value = r
        result = runner.invoke(cli_app, ["refunds", "create", "--order-id", "ord-1", "--yes"])
        assert result.exit_code == 0
        assert "Refund created" in result.output


# --- Custom fields ---


class TestCustomFields:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        f = MagicMock(id="cf-1", slug="company", name="Company", type="text", created_at="2024-01-01")
        mock_polar.custom_fields.list.return_value = make_list_result([f])
        mocker.patch("polar_cli.commands.custom_fields.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["custom-fields", "list"])
        assert result.exit_code == 0
        assert "cf-1" in result.output

    def test_delete(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["custom-fields", "delete", "cf-1", "--yes"])
        assert result.exit_code == 0
        assert "Custom field deleted" in result.output


# --- Payments ---


class TestPayments:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        p = MagicMock(id="pay-1", status="succeeded", amount=2000, currency="usd", method="card", created_at="2024-01-01")
        mock_polar.payments.list.return_value = make_list_result([p])
        mocker.patch("polar_cli.commands.payments.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["payments", "list"])
        assert result.exit_code == 0
        assert "pay-1" in result.output

    def test_get(self, runner, cli_app, mock_polar):
        p = MagicMock(id="pay-1", status="succeeded")
        mock_polar.payments.get.return_value = p
        result = runner.invoke(cli_app, ["payments", "get", "pay-1"])
        assert result.exit_code == 0
        assert "pay-1" in result.output


# --- Disputes ---


class TestDisputes:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        d = MagicMock(id="disp-1", order_id="ord-1", dispute_status="open", amount=1000, currency="usd", created_at="2024-01-01")
        mock_polar.disputes.list.return_value = make_list_result([d])
        mocker.patch("polar_cli.commands.disputes.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["disputes", "list"])
        assert result.exit_code == 0
        assert "disp-1" in result.output

    def test_get(self, runner, cli_app, mock_polar):
        d = MagicMock(id="disp-1", dispute_status="open")
        mock_polar.disputes.get.return_value = d
        result = runner.invoke(cli_app, ["disputes", "get", "disp-1"])
        assert result.exit_code == 0
        assert "disp-1" in result.output
