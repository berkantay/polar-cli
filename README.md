# Polar CLI

A command-line interface for [Polar](https://polar.sh) — manage products, customers, subscriptions, and webhooks from your terminal.

## Installation

```bash
pip install polar-cli
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install polar-cli
```

## Quick Start

```bash
# Authenticate with Polar
polar auth login

# List your products
polar products list

# Create a customer
polar customers create --email user@example.com --name "John Doe"

# Stream events in real-time
polar events stream
```

## Features

- **Full API coverage**: Products, customers, subscriptions, orders, webhooks, and more
- **Multiple output formats**: Table (default), JSON, or YAML
- **Secure authentication**: OAuth device flow with secure token storage
- **Real-time streaming**: Watch events as they happen
- **Sandbox support**: Test against sandbox environment with `--sandbox`

## Commands

```
polar auth          Authentication commands
polar products      Manage products
polar customers     Manage customers
polar subscriptions Manage subscriptions
polar orders        Manage orders
polar webhooks      Manage webhook endpoints
polar events        View and stream events
polar checkouts     Manage checkout sessions
polar discounts     Manage discounts
polar benefits      Manage benefits
polar license-keys  Manage license keys
polar meters        Manage usage meters
polar files         Manage files
polar refunds       Manage refunds
polar organizations Manage organizations
```

## Output Formats

```bash
# Default table output
polar products list

# JSON output
polar products list --output json

# YAML output
polar products list --output yaml
```

## Sandbox Mode

Test against the sandbox environment:

```bash
polar --sandbox products list
```

Or set globally:

```bash
polar config set sandbox true
```

## Configuration

Configuration is stored in `~/.config/polar-cli/` (or platform equivalent).

```bash
# View current config
polar config show

# Set default organization
polar config set default_org org_xxx

# Set default output format
polar config set output json
```

## Development

```bash
# Clone the repo
git clone https://github.com/berkantay/polar-cli
cd polar-cli

# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run the CLI
uv run polar --help
```

## License

Apache 2.0
