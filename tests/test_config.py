"""Tests for config module."""

from __future__ import annotations

import json

import pytest

from polar_cli import config
from polar_cli.config import (
    Config,
    Credentials,
    Environment,
    EnvironmentConfig,
    OutputFormat,
)


@pytest.fixture(autouse=True)
def tmp_config_dir(tmp_path, monkeypatch):
    """Redirect config to a temp directory for all tests."""
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(config, "CREDENTIALS_FILE", tmp_path / "credentials.json")
    return tmp_path


class TestLoadConfig:
    def test_creates_default_on_first_load(self, tmp_config_dir):
        cfg = config.load_config()
        assert cfg.default_environment == Environment.PRODUCTION
        assert (tmp_config_dir / "config.json").exists()

    def test_reads_existing(self, tmp_config_dir):
        data = '{"default_environment": "sandbox", "environments": {}}'
        (tmp_config_dir / "config.json").write_text(data)
        cfg = config.load_config()
        assert cfg.default_environment == Environment.SANDBOX


class TestEnvironment:
    def test_from_sandbox_flag_true(self):
        assert Environment.from_sandbox_flag(True) == Environment.SANDBOX

    def test_from_sandbox_flag_false(self):
        assert Environment.from_sandbox_flag(False) == Environment.PRODUCTION


class TestTokenManagement:
    def test_set_and_get_production_token(self):
        config.set_token(Environment.PRODUCTION, "prod-tok")
        assert config.get_token(Environment.PRODUCTION) == "prod-tok"

    def test_set_and_get_sandbox_token(self):
        config.set_token(Environment.SANDBOX, "sb-tok")
        assert config.get_token(Environment.SANDBOX) == "sb-tok"

    def test_env_var_takes_priority(self, monkeypatch):
        config.set_token(Environment.PRODUCTION, "stored")
        monkeypatch.setenv("POLAR_ACCESS_TOKEN", "env-tok")
        assert config.get_token(Environment.PRODUCTION) == "env-tok"

    def test_remove_token(self):
        config.set_token(Environment.PRODUCTION, "tok")
        config.remove_token(Environment.PRODUCTION)
        assert config.get_token(Environment.PRODUCTION) is None

    def test_credentials_file_permissions(self, tmp_config_dir):
        config.set_token(Environment.PRODUCTION, "secret")
        cred_file = tmp_config_dir / "credentials.json"
        mode = cred_file.stat().st_mode & 0o777
        assert mode == 0o600


class TestDefaultOrg:
    def test_none_by_default(self):
        assert config.get_default_org_id(Environment.PRODUCTION) is None

    def test_set_and_get(self):
        config.set_default_org_id(Environment.PRODUCTION, "org-123")
        assert config.get_default_org_id(Environment.PRODUCTION) == "org-123"

    def test_sandbox_separate(self):
        config.set_default_org_id(Environment.PRODUCTION, "prod-org")
        config.set_default_org_id(Environment.SANDBOX, "sb-org")
        assert config.get_default_org_id(Environment.PRODUCTION) == "prod-org"
        assert config.get_default_org_id(Environment.SANDBOX) == "sb-org"


class TestPydanticModels:
    def test_config_defaults(self):
        cfg = Config()
        assert cfg.default_environment == Environment.PRODUCTION
        assert Environment.PRODUCTION in cfg.environments
        assert Environment.SANDBOX in cfg.environments

    def test_config_get_env_creates_missing(self):
        cfg = Config(environments={})
        env_cfg = cfg.get_env(Environment.SANDBOX)
        assert isinstance(env_cfg, EnvironmentConfig)
        assert env_cfg.default_org_id is None

    def test_config_roundtrip_json(self):
        cfg = Config()
        cfg.get_env(Environment.PRODUCTION).default_org_id = "org-abc"
        serialized = cfg.model_dump_json()
        restored = Config.model_validate_json(serialized)
        assert restored.get_env(Environment.PRODUCTION).default_org_id == "org-abc"

    def test_credentials_defaults(self):
        creds = Credentials()
        assert creds.tokens == {}

    def test_credentials_roundtrip_json(self):
        creds = Credentials(tokens={Environment.PRODUCTION: "tok-123"})
        serialized = creds.model_dump_json()
        restored = Credentials.model_validate_json(serialized)
        assert restored.tokens[Environment.PRODUCTION] == "tok-123"

    def test_environment_config_defaults(self):
        ec = EnvironmentConfig()
        assert ec.default_org_id is None


class TestOutputFormat:
    def test_values(self):
        assert OutputFormat.TABLE == "table"
        assert OutputFormat.JSON == "json"
        assert OutputFormat.YAML == "yaml"

    def test_is_str_enum(self):
        assert isinstance(OutputFormat.TABLE, str)


class TestSaveConfig:
    def test_save_and_reload(self, tmp_config_dir):
        cfg = Config()
        cfg.get_env(Environment.PRODUCTION).default_org_id = "saved-org"
        config.save_config(cfg)

        loaded = config.load_config()
        assert loaded.get_env(Environment.PRODUCTION).default_org_id == "saved-org"

    def test_config_file_is_valid_json(self, tmp_config_dir):
        config.save_config(Config())
        raw = (tmp_config_dir / "config.json").read_text()
        data = json.loads(raw)
        assert "default_environment" in data


class TestTokenEdgeCases:
    def test_get_token_no_credentials_file(self):
        assert config.get_token(Environment.PRODUCTION) is None

    def test_remove_nonexistent_token(self):
        # Should not raise
        config.remove_token(Environment.PRODUCTION)
        assert config.get_token(Environment.PRODUCTION) is None

    def test_overwrite_token(self):
        config.set_token(Environment.PRODUCTION, "first")
        config.set_token(Environment.PRODUCTION, "second")
        assert config.get_token(Environment.PRODUCTION) == "second"

    def test_env_var_empty_string_not_used(self, monkeypatch):
        """Empty POLAR_ACCESS_TOKEN should fall through to stored token."""
        config.set_token(Environment.PRODUCTION, "stored")
        monkeypatch.setenv("POLAR_ACCESS_TOKEN", "")
        # Empty string is falsy, so get_token returns it (truthy check)
        # Actually, empty string IS returned since `if env_token:` is False for ""
        assert config.get_token(Environment.PRODUCTION) == "stored"
