"""Central configuration; constructing settings performs no network or provider work."""

from typing import Literal, Self

from pydantic import (
    HttpUrl,
    PostgresDsn,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(RuntimeError):
    """A safe startup error that never contains configuration values."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        frozen=True,
        validate_default=True,
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "test", "production"] = "development"
    provider_mode: Literal["disabled", "fixture", "real"] = "disabled"
    demo_enabled: bool = False
    watch_enabled: bool = False
    database_url: SecretStr | None = None
    identity_database_url: SecretStr | None = None
    processing_notice_version: str = "2026-10-01"
    postgres_password: SecretStr | None = None
    postgres_port: int = 5432
    supabase_url: HttpUrl | None = None
    jwt_issuer: HttpUrl | None = None
    jwt_jwks_url: HttpUrl | None = None
    jwt_audience: str = "authenticated"
    supabase_service_role_key: SecretStr | None = None
    nebius_api_key: SecretStr | None = None
    tavily_api_key: SecretStr | None = None
    deletion_hmac_key: SecretStr | None = None
    receipt_encryption_key: SecretStr | None = None

    @field_validator(
        "database_url",
        "identity_database_url",
        "postgres_password",
        "supabase_url",
        "jwt_issuer",
        "jwt_jwks_url",
        "supabase_service_role_key",
        "nebius_api_key",
        "tavily_api_key",
        "deletion_hmac_key",
        "receipt_encryption_key",
        mode="before",
    )
    @classmethod
    def empty_optional_setting(cls, value: object) -> object:
        # Empty example credentials are absent; empty environment/mode flags are invalid.
        return None if value == "" else value

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        if not 1 <= self.postgres_port <= 65535:
            raise ValueError("POSTGRES_PORT must be between 1 and 65535")
        if not self.jwt_audience.strip():
            raise ValueError("JWT_AUDIENCE must not be blank")
        if not self.processing_notice_version.strip() or len(self.processing_notice_version) > 100:
            raise ValueError("PROCESSING_NOTICE_VERSION must contain 1 to 100 characters")
        for database_url in (self.database_url, self.identity_database_url):
            if database_url is None:
                continue
            try:
                dsn = PostgresDsn(database_url.get_secret_value())
            except ValidationError:
                raise ValueError("DATABASE_URL must be a PostgreSQL psycopg URL") from None
            if dsn.scheme != "postgresql+psycopg" or not dsn.path or dsn.path == "/":
                raise ValueError("DATABASE_URL must select a psycopg driver and database")
            if any(not host.get("password") for host in dsn.hosts()):
                raise ValueError("DATABASE_URL must include a password")
        if self.identity_database_url is not None and self.database_url is not None:
            private_dsn = PostgresDsn(self.database_url.get_secret_value())
            identity_dsn = PostgresDsn(self.identity_database_url.get_secret_value())
            private_hosts, identity_hosts = private_dsn.hosts(), identity_dsn.hosts()
            if len(private_hosts) != 1 or len(identity_hosts) != 1:
                raise ValueError("Account database connections require one host")
            private_host, identity_host = private_hosts[0], identity_hosts[0]
            if private_host.get("username") == identity_host.get("username"):
                raise ValueError("Application and identity database credentials must be distinct")
            if private_dsn.path != identity_dsn.path or (
                private_host.get("host"),
                private_host.get("port", 5432),
            ) != (identity_host.get("host"), identity_host.get("port", 5432)):
                raise ValueError(
                    "Application and identity connections must select the same database"
                )
        for name in (
            "postgres_password",
            "supabase_service_role_key",
            "nebius_api_key",
            "tavily_api_key",
            "deletion_hmac_key",
            "receipt_encryption_key",
        ):
            secret = getattr(self, name)
            if secret is not None and not secret.get_secret_value().strip():
                raise ValueError(f"{name.upper()} must not be blank")
        for name in ("deletion_hmac_key", "receipt_encryption_key"):
            secret = getattr(self, name)
            if secret is not None and len(secret.get_secret_value()) < 32:
                raise ValueError(f"{name.upper()} must contain at least 32 characters")
        if (
            self.deletion_hmac_key is not None
            and self.deletion_hmac_key == self.receipt_encryption_key
        ):
            raise ValueError("Deletion and receipt secrets must be independent")
        if self.app_env == "production":
            required = (
                "database_url",
                "identity_database_url",
                "supabase_url",
                "jwt_issuer",
                "jwt_jwks_url",
                "supabase_service_role_key",
                "nebius_api_key",
                "tavily_api_key",
                "deletion_hmac_key",
                "receipt_encryption_key",
            )
            missing = [name.upper() for name in required if getattr(self, name) is None]
            if missing:
                raise ValueError("Missing production settings: " + ", ".join(missing))
            if self.provider_mode != "real":
                raise ValueError("Production requires PROVIDER_MODE=real")
            for url in (self.supabase_url, self.jwt_issuer, self.jwt_jwks_url):
                if url is not None and url.scheme != "https":
                    raise ValueError("Production service URLs must use HTTPS")
        return self


def load_settings() -> Settings:
    """Hide even malformed secret inputs from startup exception output."""
    try:
        return Settings()
    except ValidationError as error:
        messages = "; ".join(
            item["msg"]
            for item in error.errors(include_url=False, include_context=False, include_input=False)
        )
        raise ConfigurationError("Invalid configuration: " + messages) from None
