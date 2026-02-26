"""CLI error handling with clean, user-friendly error messages."""

from __future__ import annotations

import functools
import json
import sys
from typing import Any, Callable

import httpx
import typer
from polar_sdk.models import PolarError, SDKError
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console(stderr=True)


# Exit codes
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_AUTH_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_NOT_FOUND = 4
EXIT_CONNECTION_ERROR = 5


class CLIError(Exception):
    """Base class for CLI errors."""

    exit_code: int = EXIT_ERROR
    title: str = "Error"
    hint: str | None = None

    def __init__(self, message: str, hint: str | None = None) -> None:
        self.message = message
        if hint:
            self.hint = hint
        super().__init__(message)

    def render(self) -> None:
        """Render the error to stderr with a panel."""
        console.print(Panel(
            self.message,
            title=f"[bold red]{self.title}[/bold red]",
            border_style="red",
            width=60,
        ))
        if self.hint:
            console.print(f"[dim]Hint: {self.hint}[/dim]")


class AuthenticationError(CLIError):
    """Authentication failed or token is invalid."""

    exit_code = EXIT_AUTH_ERROR
    title = "Authentication error"
    hint = "Run 'polar auth login' to authenticate"


class ValidationError_(CLIError):
    """Request validation failed."""

    exit_code = EXIT_VALIDATION_ERROR
    title = "Validation error"

    def __init__(self, errors: list[tuple[str, str]], hint: str | None = None) -> None:
        self.errors = errors
        message = "\n".join(f"  {loc}: {msg}" for loc, msg in errors)
        super().__init__(message, hint)

    def render(self) -> None:
        """Render validation errors in a panel."""
        content = Text()
        for i, (loc, msg) in enumerate(self.errors):
            if i > 0:
                content.append("\n")
            content.append(f"  {loc}: ", style="bold")
            content.append(msg)
        console.print(Panel(
            content,
            title=f"[bold red]{self.title}[/bold red]",
            border_style="red",
            width=60,
        ))
        if self.hint:
            console.print(f"[dim]Hint: {self.hint}[/dim]")


class NotFoundError(CLIError):
    """Resource not found."""

    exit_code = EXIT_NOT_FOUND
    title = "Not found"


class APIError(CLIError):
    """API returned an error response."""

    exit_code = EXIT_ERROR
    title = "API error"

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        hint: str | None = None,
    ) -> None:
        self.status_code = status_code
        if status_code:
            self.title = f"API error ({status_code})"
        super().__init__(message, hint)


class ConnectionError_(CLIError):
    """Failed to connect to the API."""

    exit_code = EXIT_CONNECTION_ERROR
    title = "Connection error"
    hint = "Check your internet connection and try again"


class TimeoutError_(CLIError):
    """Request timed out."""

    exit_code = EXIT_CONNECTION_ERROR
    title = "Timeout"
    hint = "The server took too long to respond. Try again later."


def _parse_validation_errors(body: dict[str, Any]) -> list[tuple[str, str]]:
    """Parse validation errors from API response."""
    errors = []
    if "detail" in body and isinstance(body["detail"], list):
        for detail in body["detail"]:
            if isinstance(detail, dict):
                loc_parts = detail.get("loc", [])
                # Skip 'body' prefix in location
                loc_parts = [p for p in loc_parts if p != "body"]
                loc = ".".join(str(x) for x in loc_parts) or "input"
                msg = detail.get("msg", "Invalid value")
                errors.append((loc, msg))
    return errors


def _parse_pydantic_errors(exc: ValidationError) -> list[tuple[str, str]]:
    """Parse Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        loc_parts = error.get("loc", [])
        # Skip 'body' prefix
        loc_parts = [p for p in loc_parts if p != "body"]
        loc = ".".join(str(x) for x in loc_parts) or "input"
        msg = error.get("msg", "Invalid value")
        errors.append((loc, msg))
    return errors


def _parse_api_error(body: str | dict[str, Any] | None, status_code: int | None = None) -> CLIError:
    """Parse API error response into appropriate CLI error."""
    if body is None:
        return APIError("Unknown error", status_code)

    # Parse JSON string
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return APIError(body, status_code)

    if not isinstance(body, dict):
        return APIError(str(body), status_code)

    error_type = body.get("error", "")

    # Authentication errors
    if error_type in ("invalid_token", "expired_token", "Unauthorized"):
        return AuthenticationError(
            body.get("error_description", "Invalid or expired token")
        )

    # Not found errors
    if status_code == 404 or error_type == "NotFound":
        msg = body.get("detail", "Resource not found")
        if isinstance(msg, str):
            return NotFoundError(msg)
        return NotFoundError("Resource not found")

    # Validation errors
    if "detail" in body and isinstance(body["detail"], list):
        errors = _parse_validation_errors(body)
        if errors:
            return ValidationError_(errors)

    # Generic error with message
    if "detail" in body and isinstance(body["detail"], str):
        return APIError(body["detail"], status_code)

    if error_type:
        desc = body.get("error_description", body.get("detail", ""))
        msg = f"{error_type}: {desc}" if desc else error_type
        return APIError(msg, status_code)

    # Fallback: show raw JSON
    return APIError(json.dumps(body, indent=2), status_code)


def _get_hint_for_status(status_code: int | None) -> str | None:
    """Get a helpful hint based on HTTP status code."""
    hints = {
        401: "Run 'polar auth login' to authenticate",
        403: "You don't have permission for this action",
        404: "Check that the ID is correct",
        422: "Check the input values and try again",
        429: "Too many requests. Wait a moment and try again.",
        500: "Server error. Try again later.",
        502: "Service temporarily unavailable. Try again later.",
        503: "Service temporarily unavailable. Try again later.",
    }
    return hints.get(status_code) if status_code else None


def handle_errors(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that catches exceptions and renders user-friendly errors."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except (typer.Exit, typer.Abort):
            raise
        except CLIError as exc:
            exc.render()
            raise typer.Exit(exc.exit_code) from None
        except ValidationError as exc:
            errors = _parse_pydantic_errors(exc)
            cli_error = ValidationError_(errors, hint="Check the command options with --help")
            cli_error.render()
            raise typer.Exit(cli_error.exit_code) from None
        except SDKError as exc:
            cli_error = _parse_api_error(exc.body, exc.status_code)
            if not cli_error.hint:
                cli_error.hint = _get_hint_for_status(exc.status_code)
            cli_error.render()
            raise typer.Exit(cli_error.exit_code) from None
        except PolarError as exc:
            body = getattr(exc, "body", None)
            status = getattr(exc, "status_code", None)
            cli_error = _parse_api_error(body, status)
            cli_error.render()
            raise typer.Exit(cli_error.exit_code) from None
        except httpx.ConnectError:
            cli_error = ConnectionError_("Could not connect to API server")
            cli_error.render()
            raise typer.Exit(cli_error.exit_code) from None
        except httpx.TimeoutException:
            cli_error = TimeoutError_("Request timed out")
            cli_error.render()
            raise typer.Exit(cli_error.exit_code) from None
        except KeyboardInterrupt:
            console.print("\n[dim]Cancelled[/dim]")
            raise typer.Exit(130) from None
        except Exception as exc:
            # Unexpected error - show with traceback hint for debugging
            cli_error = CLIError(str(exc))
            cli_error.hint = "Run with POLAR_DEBUG=1 for more details"
            cli_error.render()
            # In debug mode, re-raise to show traceback
            if sys.stderr.isatty():
                import os
                if os.environ.get("POLAR_DEBUG"):
                    raise
            raise typer.Exit(EXIT_ERROR) from None

    return wrapper


# Export error classes for use in commands
__all__ = [
    "CLIError",
    "AuthenticationError",
    "ValidationError_",
    "NotFoundError",
    "APIError",
    "ConnectionError_",
    "TimeoutError_",
    "handle_errors",
    "EXIT_OK",
    "EXIT_ERROR",
    "EXIT_AUTH_ERROR",
    "EXIT_VALIDATION_ERROR",
    "EXIT_NOT_FOUND",
    "EXIT_CONNECTION_ERROR",
]
