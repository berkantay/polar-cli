from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from polar_cli import __version__
from polar_cli.config import Environment, OutputFormat
from polar_cli.context import CliContext

# Logo generated with: chafa --format=symbols --size=15x8 polar_logo.svg
LOGO = '\x1b[0m \x1b[38;2;0;0;0m \x1b[0m \x1b[38;2;216;216;216m▃\x1b[38;2;201;201;201m▅\x1b[38;2;208;208;208m▇\x1b[38;2;233;233;233;48;2;121;121;121m▇\x1b[0m\x1b[7m\x1b[38;2;241;241;241m▂\x1b[0m\x1b[38;2;241;241;241;48;2;126;126;126m▇\x1b[0m\x1b[38;2;237;237;237m▇\x1b[38;2;194;194;194m▅\x1b[38;2;220;220;220m▃\x1b[0m \x1b[38;2;0;0;0m  \x1b[0m\n \x1b[38;2;239;239;239m▗\x1b[7m\x1b[38;2;220;220;220m▗\x1b[0m\x1b[38;2;187;187;187m▚\x1b[7m\x1b[38;2;216;216;216m▚\x1b[38;2;197;197;197m▗\x1b[0m \x1b[38;2;7;7;7m \x1b[0m \x1b[38;2;125;125;125;48;2;254;254;254m▖\x1b[0m\x1b[38;2;230;230;230m▌\x1b[7m\x1b[38;2;218;218;218m▖\x1b[0m\x1b[38;2;226;226;226;48;2;125;125;125m▋\x1b[0m\x1b[38;2;214;214;214m▖ \x1b[0m\n\x1b[38;2;247;247;247m▗\x1b[7m\x1b[38;2;245;245;245m▗\x1b[0m\x1b[38;2;172;172;172m▗\x1b[7m\x1b[38;2;223;223;223m▗\x1b[38;2;200;200;200m▌\x1b[0m\x1b[38;2;221;221;221m▎   \x1b[7m\x1b[38;2;200;200;200m▋\x1b[0m\x1b[38;2;252;252;252;48;2;129;129;129m▉\x1b[0m \x1b[38;2;247;247;247;48;2;170;170;170m▉\x1b[0m\x1b[38;2;235;235;235m▝\x1b[38;2;250;250;250m▖\x1b[0m\n\x1b[7m\x1b[38;2;245;245;245m▏\x1b[0m\x1b[38;2;152;152;152m▎\x1b[7m\x1b[38;2;239;239;239m▎\x1b[0m\x1b[38;2;173;173;173m▎\x1b[7m\x1b[38;2;249;249;249m▎\x1b[0m\x1b[38;2;119;119;119m▏   \x1b[7m\x1b[38;2;113;113;113m▉\x1b[0m\x1b[38;2;253;253;253;48;2;229;229;229m▉\x1b[0m \x1b[7m\x1b[38;2;254;254;254m▏\x1b[0m\x1b[38;2;185;185;185m▏\x1b[38;2;241;241;241m▉\x1b[0m\n\x1b[7m\x1b[38;2;243;243;243m▏\x1b[38;2;116;116;116m▉\x1b[0m\x1b[38;2;254;254;254;48;2;164;164;164m▉\x1b[0m \x1b[38;2;255;255;255;48;2;248;248;248m┊\x1b[0m\x1b[38;2;151;151;151m▏   \x1b[0m \x1b[38;2;237;237;237m▉\x1b[7m\x1b[38;2;146;146;146m▊\x1b[0m\x1b[38;2;243;243;243m▊\x1b[7m\x1b[38;2;127;127;127m▊\x1b[0m\x1b[38;2;248;248;248m▉\x1b[0m\n\x1b[38;2;248;248;248m▝\x1b[38;2;205;205;205m▍\x1b[38;2;150;150;150;48;2;249;249;249m▏\x1b[0m\x1b[38;2;135;135;135m▏\x1b[7m\x1b[38;2;249;249;249m▏\x1b[0m\x1b[38;2;209;209;209m▍   \x1b[7m\x1b[38;2;204;204;204m▊\x1b[0m\x1b[38;2;211;211;211m▌\x1b[7m\x1b[38;2;219;219;219m▘\x1b[0m\x1b[38;2;184;184;184m▘\x1b[7m\x1b[38;2;239;239;239m▘\x1b[0m\x1b[38;2;251;251;251m▘\x1b[0m\n \x1b[38;2;216;216;216m▝\x1b[38;2;122;122;122;48;2;218;218;218m▍\x1b[0m\x1b[7m\x1b[38;2;222;222;222m▝\x1b[38;2;224;224;224m▌\x1b[0m\x1b[38;2;132;132;132;48;2;254;254;254m▝\x1b[0m \x1b[38;2;117;117;117m \x1b[0m \x1b[7m\x1b[38;2;219;219;219m▚\x1b[38;2;206;206;206m▚\x1b[0m\x1b[38;2;186;186;186m▚\x1b[7m\x1b[38;2;224;224;224m▘\x1b[0m\x1b[38;2;246;246;246m▘ \x1b[0m\n \x1b[38;2;0;0;0m \x1b[0m \x1b[7m\x1b[38;2;222;222;222m▅\x1b[38;2;192;192;192m▃\x1b[38;2;236;236;236m▁\x1b[0m\x1b[38;2;238;238;238;48;2;172;172;172m▇\x1b[0m\x1b[38;2;244;244;244m▆\x1b[38;2;232;232;232;48;2;128;128;128m▇\x1b[0m\x1b[7m\x1b[38;2;207;207;207m▁\x1b[38;2;197;197;197m▃\x1b[38;2;226;226;226m▅\x1b[0m \x1b[38;2;2;2;2m  \x1b[0m'

console = Console(no_color=True, width=60)

# Command descriptions for help display
COMMANDS = [
    ("auth", "Authenticate with Polar"),
    ("org", "Manage organizations"),
    ("products", "Manage products"),
    ("customers", "Manage customers"),
    ("orders", "Manage orders"),
    ("subscriptions", "Manage subscriptions"),
    ("webhooks", "Manage webhooks"),
    ("checkout-links", "Manage checkout links"),
    ("checkouts", "Manage checkouts"),
    ("discounts", "Manage discounts"),
    ("benefits", "Manage benefits"),
    ("license-keys", "Manage license keys"),
    ("meters", "Manage meters"),
    ("metrics", "View metrics"),
    ("events", "View events"),
    ("refunds", "Manage refunds"),
    ("custom-fields", "Manage custom fields"),
    ("payments", "Manage payments"),
    ("disputes", "Manage disputes"),
    ("benefit-grants", "Manage benefit grants"),
    ("event-types", "View event types"),
    ("files", "Manage files"),
    ("members", "Manage members"),
]

OPTIONS = [
    ("--base-url", "Custom API base URL"),
    ("--sandbox", "Use sandbox environment"),
    ("-o, --output", "Output format (table/json/yaml)"),
    ("--no-color", "Disable colored output"),
    ("-v, --verbose", "Enable verbose output"),
    ("--version", "Show version and exit"),
    ("--help", "Show this message"),
]


def render_help() -> None:
    """Render custom help with logo and organized panels."""
    print(LOGO)
    print()
    console.print(f"  Polar CLI v{__version__}")
    console.print("  https://polar.sh")
    print()
    console.print("  Usage: polar [OPTIONS] COMMAND [ARGS]...")
    print()

    # Commands table
    cmd_table = Table(show_header=False, box=None, padding=(0, 1))
    cmd_table.add_column(width=16)
    cmd_table.add_column()
    for cmd, desc in COMMANDS:
        cmd_table.add_row(cmd, desc)
    console.print(Panel(cmd_table, title="Commands", border_style="dim"))

    # Options table
    opt_table = Table(show_header=False, box=None, padding=(0, 1))
    opt_table.add_column(width=16)
    opt_table.add_column()
    for opt, desc in OPTIONS:
        opt_table.add_row(opt, desc)
    console.print(Panel(opt_table, title="Options", border_style="dim"))


app = typer.Typer(
    name="polar",
    help="",
    no_args_is_help=False,
    invoke_without_command=True,
    rich_markup_mode=None,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"polar {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    base_url: Annotated[
        str | None,
        typer.Option("--base-url", envvar="POLAR_BASE_URL", help="Custom API base URL (for self-hosted)."),
    ] = None,
    sandbox: Annotated[
        bool,
        typer.Option("--sandbox", help="Use the sandbox environment."),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format: table, json, yaml."),
    ] = OutputFormat.TABLE,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable colored output."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output."),
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True, help="Show version and exit."),
    ] = None,
) -> None:
    ctx.obj = CliContext(
        environment=Environment.from_sandbox_flag(sandbox),
        output_format=output,
        base_url=base_url,
        verbose=verbose,
        no_color=no_color,
    )
    # Show logo and help when no subcommand is provided
    if ctx.invoked_subcommand is None:
        render_help()
        raise typer.Exit(0)


# Import and register sub-commands
from polar_cli.commands.auth import app as auth_app  # noqa: E402
from polar_cli.commands.benefit_grants import app as benefit_grants_app  # noqa: E402
from polar_cli.commands.benefits import app as benefits_app  # noqa: E402
from polar_cli.commands.checkout_links import app as checkout_links_app  # noqa: E402
from polar_cli.commands.checkouts import app as checkouts_app  # noqa: E402
from polar_cli.commands.custom_fields import app as custom_fields_app  # noqa: E402
from polar_cli.commands.customers import app as customers_app  # noqa: E402
from polar_cli.commands.discounts import app as discounts_app  # noqa: E402
from polar_cli.commands.disputes import app as disputes_app  # noqa: E402
from polar_cli.commands.event_types import app as event_types_app  # noqa: E402
from polar_cli.commands.events import app as events_app  # noqa: E402
from polar_cli.commands.files import app as files_app  # noqa: E402
from polar_cli.commands.license_keys import app as license_keys_app  # noqa: E402
from polar_cli.commands.members import app as members_app  # noqa: E402
from polar_cli.commands.meters import app as meters_app  # noqa: E402
from polar_cli.commands.metrics import app as metrics_app  # noqa: E402
from polar_cli.commands.orders import app as orders_app  # noqa: E402
from polar_cli.commands.org import app as org_app  # noqa: E402
from polar_cli.commands.payments import app as payments_app  # noqa: E402
from polar_cli.commands.products import app as products_app  # noqa: E402
from polar_cli.commands.refunds import app as refunds_app  # noqa: E402
from polar_cli.commands.subscriptions import app as subscriptions_app  # noqa: E402
from polar_cli.commands.webhooks import app as webhooks_app  # noqa: E402

app.add_typer(auth_app)
app.add_typer(org_app)
app.add_typer(products_app)
app.add_typer(customers_app)
app.add_typer(orders_app)
app.add_typer(subscriptions_app)
app.add_typer(webhooks_app)
app.add_typer(checkout_links_app)
app.add_typer(checkouts_app)
app.add_typer(discounts_app)
app.add_typer(benefits_app)
app.add_typer(license_keys_app)
app.add_typer(meters_app)
app.add_typer(metrics_app)
app.add_typer(events_app)
app.add_typer(refunds_app)
app.add_typer(custom_fields_app)
app.add_typer(payments_app)
app.add_typer(disputes_app)
app.add_typer(benefit_grants_app)
app.add_typer(event_types_app)
app.add_typer(files_app)
app.add_typer(members_app)


def main() -> None:
    app()
