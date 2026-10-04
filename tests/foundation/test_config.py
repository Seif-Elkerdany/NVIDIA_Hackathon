import os
import subprocess
import sys

import pytest
from pydantic import ValidationError

from benefitbridge.config import ConfigurationError, Settings, load_settings


def test_development_does_not_enable_providers():
    settings = load_settings()
    assert settings.app_env == "development"
    assert settings.provider_mode == "disabled"
    assert settings.database_url is None


def test_dotenv_and_environment_precedence(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("APP_ENV=test\nPROVIDER_MODE=fixture\n", encoding="utf-8")
    monkeypatch.setenv("PROVIDER_MODE", "disabled")
    assert load_settings().app_env == "test"
    assert load_settings().provider_mode == "disabled"


def test_unknown_dotenv_fields_are_rejected(tmp_path):
    (tmp_path / ".env").write_text("PROVIDRE_MODE=fixture\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Extra inputs"):
        load_settings()


@pytest.mark.parametrize("name", ["APP_ENV", "PROVIDER_MODE", "DEMO_ENABLED", "POSTGRES_PORT"])
def test_empty_control_setting_does_not_silently_use_defaults(monkeypatch, name):
    monkeypatch.setenv(name, "")
    with pytest.raises(ConfigurationError):
        load_settings()


@pytest.mark.parametrize(
    "values",
    [
        {"app_env": "prod"},
        {"provider_mode": "automatic"},
        {"demo_enabled": "perhaps"},
        {"postgres_port": 0},
        {"postgres_port": 65536},
        {"jwt_audience": " "},
        {"database_url": "sqlite:///test.db"},
        {"database_url": "postgresql://user:pass@localhost/db"},
        {"database_url": "postgresql+psycopg://user:pass@localhost"},
        {"database_url": "postgresql+psycopg://user@localhost/db"},
        {"nebius_api_key": " "},
        {"deletion_hmac_key": "too-short"},
        {"unexpected": True},
    ],
)
def test_invalid_configuration_is_rejected(values):
    with pytest.raises(ValidationError):
        Settings(**values)


@pytest.mark.parametrize(
    "name",
    [
        "database_url",
        "supabase_url",
        "jwt_issuer",
        "jwt_jwks_url",
        "supabase_service_role_key",
        "nebius_api_key",
        "tavily_api_key",
        "deletion_hmac_key",
        "receipt_encryption_key",
    ],
)
def test_each_required_production_setting_fails_closed(production_values, name):
    del production_values[name]
    with pytest.raises(ValidationError, match=name.upper()):
        Settings(**production_values)


@pytest.mark.parametrize("mode", ["disabled", "fixture"])
def test_production_disallows_non_real_providers(production_values, mode):
    production_values["provider_mode"] = mode
    with pytest.raises(ValidationError, match="PROVIDER_MODE=real"):
        Settings(**production_values)


def test_complete_production_settings_validate_without_network(production_values):
    assert Settings(**production_values).app_env == "production"


@pytest.mark.parametrize("name", ["supabase_url", "jwt_issuer", "jwt_jwks_url"])
def test_production_service_urls_require_https(production_values, name):
    production_values[name] = "http://synthetic.example.invalid"
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(**production_values)


def test_independent_secrets_required(production_values):
    production_values["receipt_encryption_key"] = production_values["deletion_hmac_key"]
    with pytest.raises(ValidationError, match="independent"):
        Settings(**production_values)


def test_secrets_are_redacted(production_values):
    settings = Settings(**production_values)
    for name in ("database_url", "nebius_api_key", "supabase_service_role_key"):
        assert production_values[name] not in repr(settings)
        assert production_values[name] not in settings.model_dump_json()


def test_malformed_secret_is_not_in_startup_error(monkeypatch):
    secret = "synthetic-secret-that-must-not-leak"
    monkeypatch.setenv("DATABASE_URL", secret)
    with pytest.raises(ConfigurationError) as error:
        load_settings()
    assert secret not in str(error.value)
    assert error.value.__suppress_context__


def test_missing_production_secrets_fail_actual_process_startup():
    env = dict(os.environ, APP_ENV="production", PROVIDER_MODE="real")
    result = subprocess.run(
        [sys.executable, "-c", "from benefitbridge.main import create_app; create_app()"],
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode != 0
    assert "Missing production settings" in result.stderr
