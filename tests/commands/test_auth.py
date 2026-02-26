"""Tests for auth commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from polar_sdk.models import SDKError


def _mock_client():
    c = MagicMock()
    c.__enter__ = MagicMock(return_value=c)
    c.__exit__ = MagicMock(return_value=False)
    return c


class TestAuthLogin:
    def test_login_with_token(self, runner, cli_app, mocker):
        client = _mock_client()
        client.organizations.list.return_value.result.pagination.total_count = 2
        mocker.patch("polar_cli.commands.auth.Polar", return_value=client)
        mock_set = mocker.patch("polar_cli.commands.auth.set_token")

        result = runner.invoke(cli_app, ["auth", "login", "--token", "test-pat"])
        assert result.exit_code == 0
        assert "Logged in" in result.output
        assert "production" in result.output
        mock_set.assert_called_once()

    def test_login_prompts_when_no_token(self, runner, cli_app, mocker):
        client = _mock_client()
        client.organizations.list.return_value.result.pagination.total_count = 1
        mocker.patch("polar_cli.commands.auth.Polar", return_value=client)
        mocker.patch("polar_cli.commands.auth.set_token")

        result = runner.invoke(cli_app, ["auth", "login"], input="my-token\n")
        assert result.exit_code == 0
        assert "Logged in" in result.output

    def test_login_sandbox(self, runner, cli_app, mocker):
        client = _mock_client()
        client.organizations.list.return_value.result.pagination.total_count = 1
        mock_polar = mocker.patch("polar_cli.commands.auth.Polar", return_value=client)
        mocker.patch("polar_cli.commands.auth.set_token")

        result = runner.invoke(cli_app, ["--sandbox", "auth", "login", "--token", "sb-tok"])
        assert result.exit_code == 0
        assert "sandbox" in result.output
        # Verify SDK was called with sandbox server
        mock_polar.assert_called_once()
        _, kwargs = mock_polar.call_args
        assert kwargs.get("server") == "sandbox"

    def test_login_invalid_token_sdk_error(self, runner, cli_app, mocker):
        import httpx

        client = _mock_client()
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 401
        resp.headers = httpx.Headers()
        client.organizations.list.side_effect = SDKError("unauthorized", resp, body="Invalid token")
        mocker.patch("polar_cli.commands.auth.Polar", return_value=client)

        result = runner.invoke(cli_app, ["auth", "login", "--token", "bad-token"])
        assert result.exit_code == 1

    def test_login_with_base_url(self, runner, cli_app, mocker):
        client = _mock_client()
        client.organizations.list.return_value.result.pagination.total_count = 1
        mock_polar = mocker.patch("polar_cli.commands.auth.Polar", return_value=client)
        mocker.patch("polar_cli.commands.auth.set_token")

        result = runner.invoke(cli_app, ["--base-url", "https://my.polar.sh", "auth", "login", "--token", "tok"])
        assert result.exit_code == 0
        _, kwargs = mock_polar.call_args
        assert kwargs.get("server_url") == "https://my.polar.sh"


class TestAuthLogout:
    def test_logout_when_logged_in(self, runner, cli_app, mocker):
        mocker.patch("polar_cli.commands.auth.get_token", return_value="tok")
        mock_rm = mocker.patch("polar_cli.commands.auth.remove_token")

        result = runner.invoke(cli_app, ["auth", "logout"])
        assert result.exit_code == 0
        assert "Logged out" in result.output
        mock_rm.assert_called_once()

    def test_logout_when_not_logged_in(self, runner, cli_app, mocker):
        mocker.patch("polar_cli.commands.auth.get_token", return_value=None)

        result = runner.invoke(cli_app, ["auth", "logout"])
        assert result.exit_code == 0
        assert "Not logged in" in result.output

    def test_logout_sandbox(self, runner, cli_app, mocker):
        mocker.patch("polar_cli.commands.auth.get_token", return_value="tok")
        mocker.patch("polar_cli.commands.auth.remove_token")

        result = runner.invoke(cli_app, ["--sandbox", "auth", "logout"])
        assert result.exit_code == 0
        assert "sandbox" in result.output


class TestAuthStatus:
    def test_status_authenticated(self, runner, cli_app, mocker):
        client = _mock_client()
        org = MagicMock()
        org.name = "My Org"
        org.slug = "my-org"
        client.organizations.list.return_value.result.items = [org]

        mocker.patch("polar_cli.commands.auth.get_token", return_value="tok")
        mocker.patch("polar_cli.commands.auth.Polar", return_value=client)

        result = runner.invoke(cli_app, ["auth", "status"])
        assert result.exit_code == 0
        assert "Authenticated" in result.output
        assert "My Org" in result.output
        assert "my-org" in result.output

    def test_status_not_authenticated(self, runner, cli_app, mocker):
        mocker.patch("polar_cli.commands.auth.get_token", return_value=None)

        result = runner.invoke(cli_app, ["auth", "status"])
        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    def test_status_no_orgs(self, runner, cli_app, mocker):
        client = _mock_client()
        client.organizations.list.return_value.result.items = []

        mocker.patch("polar_cli.commands.auth.get_token", return_value="tok")
        mocker.patch("polar_cli.commands.auth.Polar", return_value=client)

        result = runner.invoke(cli_app, ["auth", "status"])
        assert result.exit_code == 0
        assert "Authenticated" in result.output

    def test_status_multiple_orgs(self, runner, cli_app, mocker):
        client = _mock_client()
        org1 = MagicMock(name="Org 1", slug="org-1")
        org2 = MagicMock(name="Org 2", slug="org-2")
        # MagicMock.name conflicts with Mock's name attr, set it explicitly
        org1.name = "Org 1"
        org2.name = "Org 2"
        client.organizations.list.return_value.result.items = [org1, org2]

        mocker.patch("polar_cli.commands.auth.get_token", return_value="tok")
        mocker.patch("polar_cli.commands.auth.Polar", return_value=client)

        result = runner.invoke(cli_app, ["auth", "status"])
        assert result.exit_code == 0
        assert "Org 1" in result.output
        assert "Org 2" in result.output
