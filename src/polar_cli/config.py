"""Token and settings storage in ~/.config/polar/ (via platformdirs)."""

from __future__ import annotations

import os
import stat
from enum import StrEnum
from pathlib import Path

from platformdirs import user_config_dir
from pydantic import BaseModel, Field

CONFIG_DIR = Path(user_config_dir("polar", ensure_exists=True))
CONFIG_FILE = CONFIG_DIR / "config.json"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"


class Environment(StrEnum):
    PRODUCTION = "production"
    SANDBOX = "sandbox"

    @classmethod
    def from_sandbox_flag(cls, sandbox: bool) -> Environment:
        return cls.SANDBOX if sandbox else cls.PRODUCTION


class EnvironmentConfig(BaseModel):
    default_org_id: str | None = None


class Config(BaseModel):
    default_environment: Environment = Environment.PRODUCTION
    environments: dict[Environment, EnvironmentConfig] = Field(
        default_factory=lambda: {
            Environment.PRODUCTION: EnvironmentConfig(),
            Environment.SANDBOX: EnvironmentConfig(),
        }
    )

    def get_env(self, env: Environment) -> EnvironmentConfig:
        return self.environments.setdefault(env, EnvironmentConfig())


class Credentials(BaseModel):
    tokens: dict[Environment, str] = Field(default_factory=dict)


class OutputFormat(StrEnum):
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"


def _write_file(path: Path, content: str, *, secure: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if secure:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def load_config() -> Config:
    if not CONFIG_FILE.exists():
        cfg = Config()
        _write_file(CONFIG_FILE, cfg.model_dump_json(indent=2) + "\n")
        return cfg
    return Config.model_validate_json(CONFIG_FILE.read_text())


def save_config(config: Config) -> None:
    _write_file(CONFIG_FILE, config.model_dump_json(indent=2) + "\n")


def get_default_org_id(env: Environment) -> str | None:
    return load_config().get_env(env).default_org_id


def set_default_org_id(env: Environment, org_id: str) -> None:
    config = load_config()
    config.get_env(env).default_org_id = org_id
    save_config(config)


def _load_credentials() -> Credentials:
    if not CREDENTIALS_FILE.exists():
        return Credentials()
    return Credentials.model_validate_json(CREDENTIALS_FILE.read_text())


def _save_credentials(credentials: Credentials) -> None:
    _write_file(CREDENTIALS_FILE, credentials.model_dump_json(indent=2) + "\n", secure=True)


def get_token(env: Environment) -> str | None:
    """Get access token. POLAR_ACCESS_TOKEN env var takes priority."""
    env_token = os.environ.get("POLAR_ACCESS_TOKEN")
    if env_token:
        return env_token
    return _load_credentials().tokens.get(env)


def set_token(env: Environment, token: str) -> None:
    creds = _load_credentials()
    creds.tokens[env] = token
    _save_credentials(creds)


def remove_token(env: Environment) -> None:
    creds = _load_credentials()
    creds.tokens.pop(env, None)
    _save_credentials(creds)
