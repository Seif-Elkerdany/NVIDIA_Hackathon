"""One forward Alembic chain, using validated configuration or a test connection.

Run migration commands with migration credentials, never the private app role.
No URL or configuration values are written to logs.
"""

from pathlib import Path

from alembic import context
from pydantic import ValidationError
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.pool import NullPool

from benefitbridge.config import ConfigurationError, Settings
from benefitbridge.db import documents, jobs, profiles, sources  # noqa: F401 -- register metadata
from benefitbridge.db.base import Base


def database_url() -> str:
    try:
        settings = Settings(_env_file=Path(__file__).resolve().parents[2] / ".env")
    except ValidationError:
        raise ConfigurationError("Invalid migration configuration") from None
    if settings.database_url is None:
        raise ConfigurationError("DATABASE_URL is required to run migrations")
    return settings.database_url.get_secret_value()


def migrate(connection: Connection) -> None:
    version = connection.scalar(text("SELECT current_setting('server_version_num')::integer"))
    if not isinstance(version, int) or version // 10000 != 17:
        raise ConfigurationError("Migrations require PostgreSQL 17")
    # The version probe and migration share the caller's transaction so schema
    # changes and the Alembic head commit or roll back together.
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=database_url(),
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    supplied = context.config.attributes.get("connection")
    if supplied is not None:
        if not isinstance(supplied, Connection):
            raise ConfigurationError("Migration connection must be a SQLAlchemy Connection")
        migrate(supplied)
    else:
        engine = create_engine(database_url(), poolclass=NullPool, hide_parameters=True)
        try:
            with engine.begin() as connection:
                migrate(connection)
        finally:
            engine.dispose()
