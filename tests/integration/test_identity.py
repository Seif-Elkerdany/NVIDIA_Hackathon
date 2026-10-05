"""Real PostgreSQL 17 isolation/constraints; BB_TEST_DB_URL is an admin test DSN.

The fixture creates and drops its own database and login roles. Never point it
at production: its configured server must be an isolated local/test cluster.
"""

import asyncio
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from benefitbridge.db.base import Base, owner_transaction, set_owner_context, subject_hmac
from benefitbridge.db.profiles import AccountRecord, FactRecord, ProfileRecord
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import ActorContext

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 10, 4, 12, tzinfo=UTC)
OWNER_A = UUID("00000000-0000-4000-8000-000000000001")
OWNER_B = UUID("00000000-0000-4000-8000-000000000002")
PROFILE_A = UUID("00000000-0000-4000-8000-000000000011")
PROFILE_B = UUID("00000000-0000-4000-8000-000000000012")
VERSION_A = UUID("00000000-0000-4000-8000-000000000021")
VERSION_B = UUID("00000000-0000-4000-8000-000000000022")
FACT_A = UUID("00000000-0000-4000-8000-000000000031")
FACT_B = UUID("00000000-0000-4000-8000-000000000032")


def run(coroutine):
    # Psycopg async requires a selector loop on Windows, also supported on Linux.
    return asyncio.run(coroutine, loop_factory=asyncio.SelectorEventLoop)


@pytest.fixture
def database():
    dsn = os.environ.get("BB_TEST_DB_URL")
    if not dsn:
        pytest.fail("MS-007 PostgreSQL gate requires BB_TEST_DB_URL for an isolated test server")
    url = make_url(dsn)
    if url.host not in {"127.0.0.1", "::1", "localhost"}:
        pytest.fail("Database fixtures require a loopback PostgreSQL test cluster")
    suffix = uuid4().hex
    name, app_role, admin_role = (f"bb_test_{kind}_{suffix}" for kind in ("db", "app", "admin"))
    role_password = "synthetic-ms007-test-role-password"
    server = create_engine(url, isolation_level="AUTOCOMMIT")
    with server.connect() as connection:
        assert (
            connection.scalar(text("SELECT current_setting('server_version_num')::int")) // 10000
            == 17
        )
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    admin = create_engine(url.set(database=name))
    try:
        with admin.begin() as connection:
            config = Config(str(ROOT / "alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version")) == "0005_budget"
            )
            # These literal values are fixture-owned, never caller-supplied SQL.
            for role in (app_role, admin_role):
                connection.execute(
                    text(
                        f'CREATE ROLE "{role}" LOGIN NOSUPERUSER NOBYPASSRLS '
                        f"PASSWORD '{role_password}'"
                    )
                )
            connection.execute(text(f'GRANT benefitbridge_app TO "{app_role}"'))
            connection.execute(text(f'GRANT benefitbridge_identity_admin TO "{admin_role}"'))
            # Test the boolean definer lookup with a non-superuser function owner.
            connection.execute(text(f'GRANT SELECT ON deleted_subjects TO "{admin_role}"'))
            connection.execute(
                text(
                    "ALTER FUNCTION benefitbridge_subject_denied(bytea, timestamptz) "
                    f'OWNER TO "{admin_role}"'
                )
            )
        app_url = url.set(database=name, username=app_role, password=role_password)
        identity_url = url.set(database=name, username=admin_role, password=role_password)
        identity = create_engine(identity_url)
        with identity.begin() as connection:
            for owner, profile, version, fact in (
                (OWNER_A, PROFILE_A, VERSION_A, FACT_A),
                (OWNER_B, PROFILE_B, VERSION_B, FACT_B),
            ):
                connection.execute(
                    text("""INSERT INTO accounts
                    (id, status, display_name, timezone, created_at)
                    VALUES (:owner, 'ACTIVE', 'Synthetic Applicant', 'UTC', :now)"""),
                    {"owner": owner, "now": NOW},
                )
                connection.execute(
                    text("INSERT INTO profiles VALUES (:profile, :owner, :version)"),
                    {"profile": profile, "owner": owner, "version": version},
                )
                connection.execute(
                    text("""INSERT INTO profile_versions
                    (id, owner_id, version_number, created_at)
                    VALUES (:version, :owner, 1, :now)"""),
                    {"version": version, "owner": owner, "now": NOW},
                )
                connection.execute(
                    text("""INSERT INTO facts
                    (id, owner_id, attribute, typed_value, provenance, confirmed_at, conflict)
                    VALUES (:fact, :owner, 'education.enrolled',
                      jsonb_build_object('type', 'BOOLEAN', 'value', true),
                      'USER_CONFIRMED', :now, false)"""),
                    {"fact": fact, "owner": owner, "now": NOW},
                )
                connection.execute(
                    text("""INSERT INTO profile_version_facts VALUES
                    (:owner, :version, :fact, 'education.enrolled')"""),
                    {"owner": owner, "version": version, "fact": fact},
                )
        identity.dispose()
        yield admin, create_engine(app_url), app_url, identity_url
    finally:
        admin.dispose()
        with server.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            for role in (app_role, admin_role):
                connection.execute(text(f'DROP ROLE IF EXISTS "{role}"'))
        server.dispose()


def context(connection, owner=OWNER_A, epoch=0):
    connection.execute(
        text(
            "SELECT set_config('app.owner_id', :owner, true), "
            "set_config('app.deletion_epoch', :epoch, true)"
        ),
        {"owner": str(owner), "epoch": str(epoch)},
    )


def test_migration_and_rls_fail_closed_and_pool_context_is_local(database):
    _, app, _, _ = database
    try:
        with app.begin() as connection:
            assert connection.scalar(text("SELECT count(*) FROM profiles")) == 0
            context(connection)
            assert connection.execute(text("SELECT id FROM profiles")).scalars().all() == [
                PROFILE_A
            ]
            assert (
                connection.scalar(
                    text("SELECT count(*) FROM facts WHERE id = :foreign"), {"foreign": FACT_B}
                )
                == 0
            )
        with app.begin() as connection:
            assert connection.scalar(text("SELECT count(*) FROM profiles")) == 0
            context(connection, OWNER_B)
            assert connection.scalar(text("SELECT id FROM profiles")) == PROFILE_B
    finally:
        app.dispose()


def test_migration_cli_reuses_persisted_head(database):
    admin, app, _, _ = database
    app.dispose()
    environment = {
        **os.environ,
        "DATABASE_URL": admin.url.set(
            password=admin.url.password or "synthetic-test-password"
        ).render_as_string(hide_password=False),
        "APP_ENV": "test",
    }
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ROOT / "alembic.ini"), "upgrade", "head"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, "Alembic CLI failed to load the persisted migration head"
    with admin.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0005_budget"


def test_migration_matches_typed_metadata_and_initial_empty_profile(database):
    admin, app, app_url, _ = database
    app.dispose()
    with admin.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    empty_owner, empty_profile, empty_version = (UUID(int=i) for i in (41, 42, 43))
    with admin.begin() as connection:
        connection.execute(
            text("""INSERT INTO accounts
            (id, status, display_name, timezone, created_at)
            VALUES (:owner, 'ACTIVE', 'Synthetic Empty Applicant', 'UTC', :now)"""),
            {"owner": empty_owner, "now": NOW},
        )
        connection.execute(
            text("INSERT INTO profiles VALUES (:profile, :owner, :version)"),
            {"profile": empty_profile, "owner": empty_owner, "version": empty_version},
        )
        connection.execute(
            text("""INSERT INTO profile_versions
            (id, owner_id, version_number, created_at)
            VALUES (:version, :owner, 1, :now)"""),
            {"version": empty_version, "owner": empty_owner, "now": NOW},
        )
        assert (
            connection.scalar(
                text("SELECT count(*) FROM profile_version_facts WHERE owner_id = :owner"),
                {"owner": empty_owner},
            )
            == 0
        )
    with pytest.raises(IntegrityError):
        with admin.begin() as connection:
            connection.execute(
                text("INSERT INTO profiles VALUES (:id, :owner, :version)"),
                {"id": uuid4(), "owner": OWNER_A, "version": VERSION_A},
            )

    async def read():
        engine = create_async_engine(app_url)
        try:
            async with owner_transaction(
                async_sessionmaker(engine), ActorContext(OWNER_A, 0, "synthetic")
            ) as session:
                account = (await session.execute(select(AccountRecord))).scalar_one()
                fact = (await session.execute(select(FactRecord))).scalar_one()
                assert account.status.value == "ACTIVE"
                assert fact.attribute.value == "education.enrolled"
                assert fact.typed_value.value is True
        finally:
            await engine.dispose()

    run(read())


def test_cross_owner_links_and_current_pointer_fail_even_for_admin(database):
    admin, app, _, _ = database
    app.dispose()
    for statement, values in (
        (
            "UPDATE profiles SET current_version_id = :foreign WHERE id = :profile",
            {"foreign": VERSION_B, "profile": PROFILE_A},
        ),
        (
            "INSERT INTO profile_version_facts VALUES "
            "(:owner, :version, :fact, 'education.enrolled')",
            {"owner": OWNER_A, "version": VERSION_A, "fact": FACT_B},
        ),
    ):
        with pytest.raises(IntegrityError):
            with admin.begin() as connection:
                if statement.startswith("INSERT"):
                    # Membership is validly assembled in its creation transaction;
                    # the owner-composite fact FK must reject the foreign fact.
                    version = uuid4()
                    connection.execute(
                        text("""INSERT INTO profile_versions
                        (id, owner_id, version_number, created_at)
                        VALUES (:id, :owner, 2, :now)"""),
                        {"id": version, "owner": OWNER_A, "now": NOW},
                    )
                    values = {**values, "version": version}
                connection.execute(text(statement), values)


def test_immutable_inputs_and_sealed_membership(database):
    admin, app, _, _ = database
    app.dispose()
    statements = (
        "UPDATE profile_versions SET version_number = 2",
        "UPDATE facts SET conflict = true",
        "DELETE FROM profile_version_facts",
        "INSERT INTO profile_version_facts VALUES (:owner, :version, :fact, 'education.enrolled')",
    )
    for statement in statements:
        with pytest.raises(DBAPIError):
            with admin.begin() as connection:
                if statement.startswith("DELETE"):
                    connection.execute(text("SET LOCAL ROLE benefitbridge_app"))
                    context(connection)
                connection.execute(
                    text(statement), {"owner": OWNER_A, "version": VERSION_A, "fact": FACT_A}
                )


def test_concurrent_version_numbers_have_one_winner(database):
    admin, app, _, _ = database
    barrier = Barrier(2)

    def insert_version():
        try:
            with app.begin() as connection:
                context(connection)
                barrier.wait(timeout=10)
                connection.execute(
                    text("""INSERT INTO profile_versions
                    (id, owner_id, version_number, created_at)
                    VALUES (:id, :owner, 2, :now)"""),
                    {"id": uuid4(), "owner": OWNER_A, "now": NOW},
                )
            return "committed"
        except IntegrityError:
            return "conflict"

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: insert_version(), range(2)))
        assert sorted(results) == ["committed", "conflict"]
        with admin.connect() as connection:
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM profile_versions "
                        "WHERE owner_id = :owner AND version_number = 2"
                    ),
                    {"owner": OWNER_A},
                )
                == 1
            )
    finally:
        app.dispose()


def test_tombstone_epoch_and_private_transaction_guard(database):
    admin, app, app_url, _ = database
    app.dispose()

    async def read(actor):
        engine = create_async_engine(app_url)
        try:
            async with owner_transaction(async_sessionmaker(engine), actor) as session:
                return (await session.execute(select(ProfileRecord.id))).scalar_one()
        finally:
            await engine.dispose()

    actor = ActorContext(OWNER_A, 0, "synthetic-request")
    assert run(read(actor)) == PROFILE_A
    with admin.begin() as connection:
        connection.execute(
            text("UPDATE accounts SET deletion_epoch = 1 WHERE id = :owner"), {"owner": OWNER_A}
        )
    with pytest.raises(DomainError) as error:
        run(read(actor))
    assert error.value.code == "NOT_FOUND"
    assert run(read(ActorContext(OWNER_A, 1, "synthetic-request"))) == PROFILE_A
    with admin.begin() as connection:
        connection.execute(
            text("UPDATE accounts SET status = 'DELETING' WHERE id = :owner"), {"owner": OWNER_A}
        )
    with pytest.raises(DomainError):
        run(read(ActorContext(OWNER_A, 1, "synthetic-request")))


def test_deletion_ledger_survives_purge_without_exposing_rows(database):
    admin, app, _, identity_url = database
    digest = subject_hmac(OWNER_A, b"synthetic-key" * 3)
    identity = create_engine(identity_url)
    try:
        with identity.begin() as connection:
            connection.execute(
                text("INSERT INTO deleted_subjects VALUES (:digest, :now, :until)"),
                {"digest": digest, "now": NOW, "until": NOW + timedelta(days=31)},
            )
            connection.execute(text("DELETE FROM accounts WHERE id = :owner"), {"owner": OWNER_A})
        with app.begin() as connection:
            assert (
                connection.scalar(
                    text("SELECT benefitbridge_subject_denied(:digest, :now)"),
                    {"digest": digest, "now": NOW},
                )
                is True
            )
            assert (
                connection.scalar(
                    text("SELECT benefitbridge_subject_denied(:digest, :now)"),
                    {"digest": digest, "now": NOW + timedelta(days=32)},
                )
                is False
            )
        with pytest.raises(DBAPIError):
            with app.begin() as connection:
                connection.execute(text("SELECT * FROM deleted_subjects"))
    finally:
        identity.dispose()
        app.dispose()


def test_owner_context_rejects_privileged_role_and_actor_switch(database):
    admin, app, app_url, identity_url = database
    app.dispose()

    async def check(url, switch):
        engine = create_async_engine(url)
        try:
            async with async_sessionmaker(engine)() as session, session.begin():
                await set_owner_context(session, ActorContext(OWNER_A, 0, "synthetic"))
                if switch:
                    await set_owner_context(session, ActorContext(OWNER_B, 0, "synthetic"))
        finally:
            await engine.dispose()

    with pytest.raises(RuntimeError, match="RLS bypass"):
        run(check(admin.url, False))
    with pytest.raises(RuntimeError, match="identity-administration"):
        run(check(identity_url, False))
    with pytest.raises(RuntimeError, match="change its verified owner"):
        run(check(app_url, True))
