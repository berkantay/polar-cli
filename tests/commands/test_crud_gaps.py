"""Tests for missing get/update/create on existing resources.

Covers: benefits, checkout-links, checkouts, custom-fields, discounts,
license-keys, org, products, webhooks.
"""

from unittest.mock import MagicMock

from tests.conftest import make_list_result


# --- benefits: create, update, grants ---


class TestBenefitsCreate:
    def test_create(self, runner, cli_app, mock_polar, mocker):
        b = MagicMock(id="ben-new")
        mock_polar.benefits.create.return_value = b
        mocker.patch("polar_cli.commands.benefits.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["benefits", "create", "--description", "Early access"])
        assert result.exit_code == 0
        assert "Benefit created" in result.output


class TestBenefitsUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        b = MagicMock(id="ben-1")
        mock_polar.benefits.update.return_value = b
        result = runner.invoke(cli_app, ["benefits", "update", "ben-1", "--description", "Updated"])
        assert result.exit_code == 0
        assert "Benefit updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["benefits", "update", "ben-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


class TestBenefitsGrants:
    def test_grants(self, runner, cli_app, mock_polar):
        g = MagicMock(id="bg-1", benefit_id="ben-1", customer_id="c-1", is_granted=True, created_at="2024-01-01")
        mock_polar.benefits.grants.return_value = make_list_result([g])
        result = runner.invoke(cli_app, ["benefits", "grants", "ben-1"])
        assert result.exit_code == 0
        assert "bg-1" in result.output


# --- checkout-links: get, update ---


class TestCheckoutLinksGet:
    def test_get(self, runner, cli_app, mock_polar):
        link = MagicMock(id="cl-1")
        mock_polar.checkout_links.get.return_value = link
        result = runner.invoke(cli_app, ["checkout-links", "get", "cl-1"])
        assert result.exit_code == 0


class TestCheckoutLinksUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        link = MagicMock(id="cl-1")
        mock_polar.checkout_links.update.return_value = link
        result = runner.invoke(cli_app, ["checkout-links", "update", "cl-1", "--label", "New label"])
        assert result.exit_code == 0
        assert "Checkout link updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["checkout-links", "update", "cl-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


# --- checkouts: get, update ---


class TestCheckoutsGet:
    def test_get(self, runner, cli_app, mock_polar):
        co = MagicMock(id="co-1")
        mock_polar.checkouts.get.return_value = co
        result = runner.invoke(cli_app, ["checkouts", "get", "co-1"])
        assert result.exit_code == 0


class TestCheckoutsUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        co = MagicMock(id="co-1")
        mock_polar.checkouts.update.return_value = co
        result = runner.invoke(cli_app, ["checkouts", "update", "co-1", "--customer-email", "a@b.com"])
        assert result.exit_code == 0
        assert "Checkout updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["checkouts", "update", "co-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


# --- custom-fields: create, get, update ---


class TestCustomFieldsCreate:
    def test_create(self, runner, cli_app, mock_polar, mocker):
        f = MagicMock(id="cf-new")
        mock_polar.custom_fields.create.return_value = f
        mocker.patch("polar_cli.commands.custom_fields.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["custom-fields", "create", "--name", "Company", "--slug", "company"])
        assert result.exit_code == 0
        assert "Custom field created" in result.output


class TestCustomFieldsGet:
    def test_get(self, runner, cli_app, mock_polar):
        f = MagicMock(id="cf-1")
        mock_polar.custom_fields.get.return_value = f
        result = runner.invoke(cli_app, ["custom-fields", "get", "cf-1"])
        assert result.exit_code == 0


class TestCustomFieldsUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        existing = MagicMock(type="text")
        mock_polar.custom_fields.get.return_value = existing
        updated = MagicMock(id="cf-1")
        mock_polar.custom_fields.update.return_value = updated
        result = runner.invoke(cli_app, ["custom-fields", "update", "cf-1", "--name", "New Name"])
        assert result.exit_code == 0
        assert "Custom field updated" in result.output


# --- discounts: get, update ---


class TestDiscountsGet:
    def test_get(self, runner, cli_app, mock_polar):
        d = MagicMock(id="disc-1")
        mock_polar.discounts.get.return_value = d
        result = runner.invoke(cli_app, ["discounts", "get", "disc-1"])
        assert result.exit_code == 0


class TestDiscountsUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        d = MagicMock(id="disc-1")
        mock_polar.discounts.update.return_value = d
        result = runner.invoke(cli_app, ["discounts", "update", "disc-1", "--name", "Updated"])
        assert result.exit_code == 0
        assert "Discount updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["discounts", "update", "disc-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


# --- license-keys: get, update, activate, deactivate, get-activation ---


class TestLicenseKeysGet:
    def test_get(self, runner, cli_app, mock_polar):
        lk = MagicMock(id="lk-1")
        mock_polar.license_keys.get.return_value = lk
        result = runner.invoke(cli_app, ["license-keys", "get", "lk-1"])
        assert result.exit_code == 0


class TestLicenseKeysUpdate:
    def test_update_status(self, runner, cli_app, mock_polar):
        lk = MagicMock(id="lk-1")
        mock_polar.license_keys.update.return_value = lk
        result = runner.invoke(cli_app, ["license-keys", "update", "lk-1", "--status", "disabled"])
        assert result.exit_code == 0
        assert "License key updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["license-keys", "update", "lk-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


class TestLicenseKeysActivate:
    def test_activate(self, runner, cli_app, mock_polar, mocker):
        act = MagicMock(id="act-1")
        mock_polar.license_keys.activate.return_value = act
        mocker.patch("polar_cli.commands.license_keys.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["license-keys", "activate", "--key", "AAAA-BBBB", "--label", "machine-1"])
        assert result.exit_code == 0
        assert "Activated" in result.output


class TestLicenseKeysDeactivate:
    def test_deactivate(self, runner, cli_app, mock_polar, mocker):
        mocker.patch("polar_cli.commands.license_keys.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, [
            "license-keys", "deactivate",
            "--key", "AAAA-BBBB", "--activation-id", "act-1",
        ])
        assert result.exit_code == 0
        assert "Deactivated" in result.output


class TestLicenseKeysGetActivation:
    def test_get_activation(self, runner, cli_app, mock_polar):
        act = MagicMock(id="act-1")
        mock_polar.license_keys.get_activation.return_value = act
        result = runner.invoke(cli_app, ["license-keys", "get-activation", "lk-1", "act-1"])
        assert result.exit_code == 0


# --- org: create, update ---


class TestOrgCreate:
    def test_create(self, runner, cli_app, mock_polar):
        org = MagicMock(id="org-new", name="New Org", slug="new-org")
        mock_polar.organizations.create.return_value = org
        result = runner.invoke(cli_app, ["org", "create", "--name", "New Org"])
        assert result.exit_code == 0
        assert "Organization created" in result.output


class TestOrgUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        org = MagicMock(id="org-1", name="Updated", slug="updated")
        mock_polar.organizations.update.return_value = org
        result = runner.invoke(cli_app, ["org", "update", "org-1", "--name", "Updated"])
        assert result.exit_code == 0
        assert "Organization updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["org", "update", "org-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


# --- products: update-benefits ---


class TestProductsUpdateBenefits:
    def test_update_benefits(self, runner, cli_app, mock_polar):
        product = MagicMock(id="prod-1")
        mock_polar.products.update_benefits.return_value = product
        result = runner.invoke(cli_app, [
            "products", "update-benefits", "prod-1",
            "--benefit", "ben-1", "--benefit", "ben-2",
        ])
        assert result.exit_code == 0
        assert "Benefits updated" in result.output
        call_kwargs = mock_polar.products.update_benefits.call_args[1]
        assert len(call_kwargs["product_benefits_update"]["benefits"]) == 2


# --- webhooks: get-endpoint, update-endpoint, reset-secret ---


class TestWebhooksGetEndpoint:
    def test_get(self, runner, cli_app, mock_polar):
        ep = MagicMock(id="ep-1")
        mock_polar.webhooks.get_webhook_endpoint.return_value = ep
        result = runner.invoke(cli_app, ["webhooks", "get-endpoint", "ep-1"])
        assert result.exit_code == 0


class TestWebhooksUpdateEndpoint:
    def test_update(self, runner, cli_app, mock_polar):
        ep = MagicMock(id="ep-1")
        mock_polar.webhooks.update_webhook_endpoint.return_value = ep
        result = runner.invoke(cli_app, ["webhooks", "update-endpoint", "ep-1", "--url", "https://new.example.com"])
        assert result.exit_code == 0
        assert "Endpoint updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["webhooks", "update-endpoint", "ep-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


class TestWebhooksResetSecret:
    def test_reset(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["webhooks", "reset-secret", "ep-1", "--yes"])
        assert result.exit_code == 0
        assert "Secret reset" in result.output
        mock_polar.webhooks.reset_webhook_endpoint_secret.assert_called_once()
