"""Tests for the 4 entirely new command groups: event-types, files, members, meters (full CRUD).

Also covers: meters get/create/update/quantities (only list was tested before).
"""

from unittest.mock import MagicMock

from tests.conftest import make_list_result


# --- event-types: list, update ---


class TestEventTypesList:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        et = MagicMock(name="page.view", source="api", created_at="2024-01-01")
        et.name = "page.view"  # MagicMock.name conflicts
        mock_polar.event_types.list.return_value = make_list_result([et])
        mocker.patch("polar_cli.commands.event_types.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["event-types", "list"])
        assert result.exit_code == 0


class TestEventTypesUpdate:
    def test_update_archive(self, runner, cli_app, mock_polar):
        et = MagicMock()
        mock_polar.event_types.update.return_value = et
        result = runner.invoke(cli_app, ["event-types", "update", "et-1", "--is-archived"])
        assert result.exit_code == 0
        assert "Event type updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["event-types", "update", "et-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


# --- files: list, create, update, delete ---


class TestFilesList:
    def test_list(self, runner, cli_app, mock_polar, mocker):
        f = MagicMock(id="f-1", name="readme.pdf", size=1024, mime_type="application/pdf", service="downloadable", created_at="2024-01-01")
        f.name = "readme.pdf"
        mock_polar.files.list.return_value = make_list_result([f])
        mocker.patch("polar_cli.commands.files.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, ["files", "list"])
        assert result.exit_code == 0
        assert "f-1" in result.output


class TestFilesCreate:
    def test_create(self, runner, cli_app, mock_polar, mocker):
        f = MagicMock(id="f-new")
        mock_polar.files.create.return_value = f
        mocker.patch("polar_cli.commands.files.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, [
            "files", "create",
            "--name", "doc.pdf", "--mime-type", "application/pdf", "--size", "2048",
        ])
        assert result.exit_code == 0
        assert "File entry created" in result.output


class TestFilesUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        f = MagicMock(id="f-1")
        mock_polar.files.update.return_value = f
        result = runner.invoke(cli_app, ["files", "update", "f-1", "--name", "new-name.pdf"])
        assert result.exit_code == 0
        assert "File updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["files", "update", "f-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


class TestFilesDelete:
    def test_delete(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["files", "delete", "f-1", "--yes"])
        assert result.exit_code == 0
        assert "File deleted" in result.output
        mock_polar.files.delete.assert_called_once()


# --- members: list, get, create, update, delete ---


class TestMembersList:
    def test_list(self, runner, cli_app, mock_polar):
        m = MagicMock(id="m-1", customer_id="c-1", created_at="2024-01-01")
        mock_polar.members.list_members.return_value = make_list_result([m])
        result = runner.invoke(cli_app, ["members", "list"])
        assert result.exit_code == 0
        assert "m-1" in result.output


class TestMembersGet:
    def test_get(self, runner, cli_app, mock_polar):
        m = MagicMock(id="m-1")
        mock_polar.members.get_member.return_value = m
        result = runner.invoke(cli_app, ["members", "get", "m-1"])
        assert result.exit_code == 0


class TestMembersCreate:
    def test_create(self, runner, cli_app, mock_polar):
        m = MagicMock(id="m-new")
        mock_polar.members.create_member.return_value = m
        result = runner.invoke(cli_app, ["members", "create", "--customer-id", "c-1"])
        assert result.exit_code == 0
        assert "Member created" in result.output


class TestMembersUpdate:
    def test_update_name(self, runner, cli_app, mock_polar):
        m = MagicMock(id="m-1")
        mock_polar.members.update_member.return_value = m
        result = runner.invoke(cli_app, ["members", "update", "m-1", "--name", "New Name"])
        assert result.exit_code == 0
        assert "Member updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["members", "update", "m-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


class TestMembersDelete:
    def test_delete(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["members", "delete", "m-1", "--yes"])
        assert result.exit_code == 0
        assert "Member deleted" in result.output
        mock_polar.members.delete_member.assert_called_once()


# --- meters: get, create, update, quantities ---


class TestMetersGet:
    def test_get(self, runner, cli_app, mock_polar):
        m = MagicMock(id="meter-1")
        mock_polar.meters.get.return_value = m
        result = runner.invoke(cli_app, ["meters", "get", "meter-1"])
        assert result.exit_code == 0


class TestMetersCreate:
    def test_create(self, runner, cli_app, mock_polar, mocker):
        m = MagicMock(id="meter-new")
        mock_polar.meters.create.return_value = m
        mocker.patch("polar_cli.commands.meters.resolve_org_id", return_value="org-1")
        result = runner.invoke(cli_app, [
            "meters", "create",
            "--name", "API Calls",
            "--filter", '{"name": "api.call"}',
            "--aggregation", '{"func": "count"}',
        ])
        assert result.exit_code == 0
        assert "Meter created" in result.output


class TestMetersUpdate:
    def test_update(self, runner, cli_app, mock_polar):
        m = MagicMock(id="meter-1")
        mock_polar.meters.update.return_value = m
        result = runner.invoke(cli_app, ["meters", "update", "meter-1", "--name", "Renamed"])
        assert result.exit_code == 0
        assert "Meter updated" in result.output

    def test_update_nothing(self, runner, cli_app, mock_polar):
        result = runner.invoke(cli_app, ["meters", "update", "meter-1"])
        assert result.exit_code == 0
        assert "Nothing to update" in result.output


class TestMetersQuantities:
    def test_quantities(self, runner, cli_app, mock_polar):
        result_data = MagicMock()
        result_data.model_dump.return_value = {"timestamps": [], "values": []}
        mock_polar.meters.quantities.return_value = result_data
        result = runner.invoke(cli_app, [
            "meters", "quantities", "meter-1",
            "--start", "2024-01-01T00:00:00", "--end", "2024-02-01T00:00:00",
        ])
        assert result.exit_code == 0
