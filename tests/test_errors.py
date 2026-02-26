"""Tests for error handler decorator and error classes."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import httpx
import pytest
import typer
from polar_sdk.models import PolarError, SDKError
from pydantic import BaseModel, ValidationError

from polar_cli.errors import (
    APIError,
    AuthenticationError,
    CLIError,
    ConnectionError_,
    NotFoundError,
    TimeoutError_,
    ValidationError_,
    _parse_api_error,
    _parse_pydantic_errors,
    _parse_validation_errors,
    handle_errors,
    EXIT_AUTH_ERROR,
    EXIT_CONNECTION_ERROR,
    EXIT_ERROR,
    EXIT_NOT_FOUND,
    EXIT_VALIDATION_ERROR,
)


class TestHandleErrors:
    def test_passes_through_on_success(self):
        @handle_errors
        def ok():
            return 42

        assert ok() == 42

    def test_reraises_typer_exit(self):
        @handle_errors
        def exits():
            raise typer.Exit(0)

        with pytest.raises(typer.Exit):
            exits()

    def test_reraises_typer_abort(self):
        @handle_errors
        def aborts():
            raise typer.Abort()

        with pytest.raises(typer.Abort):
            aborts()

    def test_catches_sdk_error(self):
        @handle_errors
        def api_fail():
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 404
            resp.headers = httpx.Headers()
            raise SDKError("not found", resp, body='{"detail":"Not found"}')

        with pytest.raises(typer.Exit):
            api_fail()

    def test_catches_polar_error(self):
        @handle_errors
        def sdk_fail():
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 422
            resp.headers = httpx.Headers()
            raise PolarError("something broke", resp)

        with pytest.raises(typer.Exit):
            sdk_fail()

    def test_catches_connect_error(self):
        @handle_errors
        def conn_fail():
            raise httpx.ConnectError("connection refused")

        with pytest.raises(typer.Exit):
            conn_fail()

    def test_catches_timeout(self):
        @handle_errors
        def timeout_fail():
            raise httpx.ReadTimeout("read timed out")

        with pytest.raises(typer.Exit):
            timeout_fail()

    def test_catches_generic_exception(self):
        @handle_errors
        def generic_fail():
            raise ValueError("unexpected")

        with pytest.raises(typer.Exit):
            generic_fail()

    def test_preserves_function_name(self):
        @handle_errors
        def my_func():
            pass

        assert my_func.__name__ == "my_func"

    def test_keyboard_interrupt(self):
        @handle_errors
        def interrupt_func():
            raise KeyboardInterrupt()

        with pytest.raises(typer.Exit) as exc_info:
            interrupt_func()
        assert exc_info.value.exit_code == 130


class TestCLIError:
    def test_basic_error(self):
        err = CLIError("Something went wrong")
        assert err.message == "Something went wrong"
        assert err.exit_code == EXIT_ERROR
        assert err.title == "Error"
        assert err.hint is None

    def test_error_with_hint(self):
        err = CLIError("Failed", hint="Try again")
        assert err.message == "Failed"
        assert err.hint == "Try again"


class TestAuthenticationError:
    def test_defaults(self):
        err = AuthenticationError("Invalid token")
        assert err.exit_code == EXIT_AUTH_ERROR
        assert err.title == "Authentication error"
        assert "polar auth login" in err.hint


class TestValidationError:
    def test_single_error(self):
        err = ValidationError_([("email", "Invalid format")])
        assert err.exit_code == EXIT_VALIDATION_ERROR
        assert len(err.errors) == 1
        assert err.errors[0] == ("email", "Invalid format")

    def test_multiple_errors(self):
        errors = [
            ("email", "Invalid format"),
            ("name", "Required"),
        ]
        err = ValidationError_(errors)
        assert len(err.errors) == 2


class TestNotFoundError:
    def test_defaults(self):
        err = NotFoundError("Customer not found")
        assert err.exit_code == EXIT_NOT_FOUND
        assert err.title == "Not found"


class TestAPIError:
    def test_without_status(self):
        err = APIError("Server error")
        assert err.exit_code == EXIT_ERROR
        assert err.title == "API error"

    def test_with_status(self):
        err = APIError("Forbidden", status_code=403)
        assert err.title == "API error (403)"


class TestConnectionError:
    def test_defaults(self):
        err = ConnectionError_("Cannot connect")
        assert err.exit_code == EXIT_CONNECTION_ERROR
        assert "internet connection" in err.hint


class TestTimeoutError:
    def test_defaults(self):
        err = TimeoutError_("Timed out")
        assert err.exit_code == EXIT_CONNECTION_ERROR
        assert "too long" in err.hint


class TestParseValidationErrors:
    def test_parse_detail_list(self):
        body = {
            "detail": [
                {"loc": ["body", "email"], "msg": "Invalid email"},
                {"loc": ["body", "name"], "msg": "Required"},
            ]
        }
        errors = _parse_validation_errors(body)
        assert len(errors) == 2
        assert errors[0] == ("email", "Invalid email")
        assert errors[1] == ("name", "Required")

    def test_skip_body_prefix(self):
        body = {"detail": [{"loc": ["body", "field"], "msg": "Error"}]}
        errors = _parse_validation_errors(body)
        assert errors[0][0] == "field"

    def test_empty_detail(self):
        body = {"detail": []}
        errors = _parse_validation_errors(body)
        assert errors == []


class TestParsePydanticErrors:
    def test_parse_errors(self):
        class Model(BaseModel):
            email: str
            count: int

        try:
            Model(email=123, count="abc")  # type: ignore
        except ValidationError as exc:
            errors = _parse_pydantic_errors(exc)
            assert len(errors) == 2


class TestParseAPIError:
    def test_none_body(self):
        err = _parse_api_error(None, 500)
        assert isinstance(err, APIError)
        assert "Unknown error" in err.message

    def test_string_body(self):
        err = _parse_api_error("Something failed", 500)
        assert isinstance(err, APIError)
        assert err.message == "Something failed"

    def test_json_string_body(self):
        body = json.dumps({"detail": "Not found"})
        err = _parse_api_error(body, 404)
        assert isinstance(err, NotFoundError)

    def test_invalid_token(self):
        body = {"error": "invalid_token", "error_description": "Token expired"}
        err = _parse_api_error(body, 401)
        assert isinstance(err, AuthenticationError)

    def test_expired_token(self):
        body = {"error": "expired_token"}
        err = _parse_api_error(body, 401)
        assert isinstance(err, AuthenticationError)

    def test_not_found_by_status(self):
        body = {"detail": "Resource not found"}
        err = _parse_api_error(body, 404)
        assert isinstance(err, NotFoundError)

    def test_not_found_by_error_type(self):
        body = {"error": "NotFound", "detail": "Customer not found"}
        err = _parse_api_error(body, 404)
        assert isinstance(err, NotFoundError)

    def test_validation_errors(self):
        body = {
            "detail": [
                {"loc": ["body", "email"], "msg": "Invalid"},
            ]
        }
        err = _parse_api_error(body, 422)
        assert isinstance(err, ValidationError_)

    def test_generic_error_with_type(self):
        body = {"error": "rate_limit", "error_description": "Too many requests"}
        err = _parse_api_error(body, 429)
        assert isinstance(err, APIError)
        assert "rate_limit" in err.message
