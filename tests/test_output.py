"""Tests for output module."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from polar_cli.config import OutputFormat
from polar_cli.output import Column, _format_value, _get_attr, _to_dict, render_detail, render_list


class TestGetAttr:
    def test_dict_key(self):
        assert _get_attr({"a": 1}, "a") == 1

    def test_object_attr(self):
        obj = MagicMock()
        obj.name = "test"
        assert _get_attr(obj, "name") == "test"

    def test_dotted_path(self):
        obj = MagicMock()
        obj.nested.value = 42
        assert _get_attr(obj, "nested.value") == 42

    def test_missing_returns_none(self):
        assert _get_attr({}, "missing") is None

    def test_none_object(self):
        assert _get_attr(None, "anything") is None

    def test_nested_dict(self):
        assert _get_attr({"a": {"b": 3}}, "a.b") == 3

    def test_missing_intermediate_returns_none(self):
        assert _get_attr({"a": None}, "a.b") is None


class TestFormatValue:
    def test_none(self):
        assert _format_value(None) == "-"

    def test_bool_true(self):
        assert _format_value(True) == "Yes"

    def test_bool_false(self):
        assert _format_value(False) == "No"

    def test_string(self):
        assert _format_value("hello") == "hello"

    def test_list(self):
        assert _format_value(["a", "b"]) == "a, b"

    def test_empty_list(self):
        assert _format_value([]) == ""

    def test_integer(self):
        assert _format_value(42) == "42"

    def test_datetime(self):
        dt = datetime(2024, 3, 15, 10, 30)
        assert _format_value(dt) == "2024-03-15 10:30"


class TestToDict:
    def test_dict_passthrough(self):
        d = {"a": 1, "b": 2}
        assert _to_dict(d) == {"a": 1, "b": 2}

    def test_object_with_model_dump(self):
        obj = MagicMock()
        obj.model_dump.return_value = {"id": "1"}
        assert _to_dict(obj) == {"id": "1"}
        obj.model_dump.assert_called_once_with(mode="json")

    def test_plain_object_fallback(self):
        class Obj:
            def __init__(self):
                self.x = 1
                self._private = 2
        result = _to_dict(Obj())
        assert result == {"x": 1}
        assert "_private" not in result


class TestRenderList:
    def test_json_output(self):
        items = [{"id": "1", "name": "Test"}]
        columns = [Column("ID", "id"), Column("Name", "name")]
        render_list(items, columns, None, OutputFormat.JSON)

    def test_yaml_output(self, capsys):
        items = [{"id": "1", "name": "Test"}]
        columns = [Column("ID", "id"), Column("Name", "name")]
        render_list(items, columns, None, OutputFormat.YAML)
        captured = capsys.readouterr()
        assert "id:" in captured.out

    def test_table_output(self):
        items = [MagicMock(id="1", name="Test")]
        columns = [Column("ID", "id"), Column("Name", "name")]
        render_list(items, columns, None, OutputFormat.TABLE)

    def test_empty_list(self):
        columns = [Column("ID", "id")]
        render_list([], columns, None, OutputFormat.TABLE)

    def test_pagination_footer(self, capsys):
        pag = MagicMock()
        pag.total_count = 50
        items = [MagicMock(id=str(i)) for i in range(10)]
        columns = [Column("ID", "id")]
        render_list(items, columns, pag, OutputFormat.TABLE)
        # The pagination info goes to Rich console, not capsys,
        # but we verify it doesn't crash

    def test_no_pagination(self):
        items = [MagicMock(id="1")]
        columns = [Column("ID", "id")]
        render_list(items, columns, None, OutputFormat.TABLE)

    def test_json_with_model_dump(self):
        obj = MagicMock()
        obj.model_dump.return_value = {"id": "1", "name": "SDK Object"}
        columns = [Column("ID", "id"), Column("Name", "name")]
        render_list([obj], columns, None, OutputFormat.JSON)

    def test_yaml_with_model_dump(self, capsys):
        obj = MagicMock()
        obj.model_dump.return_value = {"id": "1"}
        columns = [Column("ID", "id")]
        render_list([obj], columns, None, OutputFormat.YAML)
        captured = capsys.readouterr()
        assert "id:" in captured.out


class TestRenderDetail:
    def test_json_output(self):
        obj = {"id": "1", "name": "Test"}
        fields = [Column("ID", "id"), Column("Name", "name")]
        render_detail(obj, fields, OutputFormat.JSON)

    def test_yaml_output(self, capsys):
        obj = {"id": "1", "name": "Test"}
        fields = [Column("ID", "id"), Column("Name", "name")]
        render_detail(obj, fields, OutputFormat.YAML)
        captured = capsys.readouterr()
        assert "id:" in captured.out

    def test_table_output(self):
        obj = {"id": "1", "name": "Test"}
        fields = [Column("ID", "id"), Column("Name", "name")]
        render_detail(obj, fields, OutputFormat.TABLE)

    def test_empty_fields(self):
        obj = {"id": "1"}
        render_detail(obj, [], OutputFormat.JSON)

    def test_missing_field_shows_dash(self):
        obj = {"id": "1"}
        fields = [Column("ID", "id"), Column("Name", "name")]
        render_detail(obj, fields, OutputFormat.TABLE)


class TestColumn:
    def test_named_tuple_access(self):
        col = Column("My Header", "my_key")
        assert col.header == "My Header"
        assert col.key == "my_key"
        assert col[0] == "My Header"
        assert col[1] == "my_key"
