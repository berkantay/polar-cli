"""Tests for the root app — global flags, version, help."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from polar_cli import __version__
from polar_cli.app import app

runner = CliRunner()

# Regex to strip ANSI escape codes from Rich output
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_RE.sub("", text)


class TestVersion:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert f"polar {__version__}" in result.output


class TestHelp:
    def test_no_args_shows_usage(self):
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_help_flag(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--sandbox" in output
        assert "--output" in output
        assert "--base-url" in output


class TestOutputValidation:
    def test_invalid_output_format_rejected(self):
        result = runner.invoke(app, ["--output", "xml", "org", "list"])
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    def test_valid_output_formats_accepted(self):
        # These will fail with auth errors, but the important thing is
        # they don't fail with "Invalid value" for --output
        for fmt in ("table", "json", "yaml"):
            result = runner.invoke(app, ["--output", fmt, "org", "list"])
            assert "Invalid value" not in result.output


class TestSandboxFlag:
    def test_sandbox_flag_accepted(self):
        result = runner.invoke(app, ["--sandbox", "auth", "status"])
        # Will fail with "Not authenticated" but sandbox flag itself is fine
        assert "Invalid" not in result.output


class TestSubcommandHelp:
    def test_all_commands_have_help(self):
        commands = [
            "auth", "org", "products", "customers", "orders",
            "subscriptions", "webhooks", "checkout-links", "checkouts",
            "discounts", "benefits", "license-keys", "meters",
            "metrics", "events", "refunds", "custom-fields",
            "payments", "disputes", "benefit-grants", "event-types",
            "files", "members",
        ]
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"{cmd} --help failed: {result.output}"
