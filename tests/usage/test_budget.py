"""Synthetic registry quotation; no provider calls or fabricated billing."""

# Real PostgreSQL acceptance checks reuse the MS-005 harness and M1 tenancy fixture.
import asyncio
from contextlib import contextmanager
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, delete, insert, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from tests.fakes.providers import FakeClock
from tests.inference.test_registry import model, registry
from tests.integration import test_identity as identity
from tests.integration import test_jobs as jobs

from benefitbridge.db.budget import BudgetChargeRecord
from benefitbridge.db.jobs import RunRecord, UsageEntryRecord, UsageReservationRecord
from benefitbridge.db.profiles import AccountRecord
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import ActorContext, ModelRole, ProviderUsage
from benefitbridge.usage.budget import (
    BudgetLimits,
    BudgetService,
    ProviderCostQuote,
    RetainedChargeReconciler,
    quote_model_call,
)

database = identity.database


@contextmanager
def expect_error(code):
    with pytest.raises(DomainError) as error:
        yield
    assert error.value.code == code


def fixed_quote(amount=100):
    return ProviderCostQuote(
        provider="synthetic-search",
        registry_version="synthetic-registry-v1",
        price_version="synthetic-price-v1",
        maximum_microusd=amount,
    )


@pytest.fixture
def funded(database):
    admin, _, url, _ = database
    clock = FakeClock()
    runs = [
        jobs.run_values(clock, owner=owner)
        for owner in (identity.OWNER_A, identity.OWNER_A, identity.OWNER_B)
    ]
    with admin.begin() as connection:
        connection.execute(insert(RunRecord), runs)
    yield admin, url, clock, runs
    database[1].dispose()


def execute(funded, body, **caps):
    async def scenario():
        admin, url, clock, runs = funded
        engine = create_async_engine(url)
        sessions = async_sessionmaker(engine, expire_on_commit=False)

        def service(index=0):
            return BudgetService(
                sessions,
                clock,
                limits(**caps),
                actor=ActorContext(runs[index]["owner_id"], 0, "synthetic-budget-test"),
            )

        try:
            return await body(service, runs, clock, admin)
        finally:
            await engine.dispose()

    return identity.run(scenario())


@pytest.mark.integration
@pytest.mark.parametrize(
    "indices,caps,code,count",
    [
        ([0, 2] * 5, {"global_daily_microusd": 200}, "BUDGET_EXCEEDED", 2),
        ([0, 1] * 5, {"owner_daily_microusd": 200}, "BUDGET_EXCEEDED", 2),
        ([0] * 10, {"run_microusd": 200}, "BUDGET_EXCEEDED", 2),
        ([0, 2] * 5, {"global_concurrency": 2}, "CONCURRENCY_LIMIT", 2),
        ([0, 1] * 5, {"owner_concurrency": 2}, "CONCURRENCY_LIMIT", 2),
        ([0] * 10, {"run_concurrency": 1}, "CONCURRENCY_LIMIT", 1),
    ],
)
def test_concurrent_reservations_enforce_every_money_and_concurrency_cap(
    funded, indices, caps, code, count
):
    async def scenario(service, runs, clock, admin):
        results = await asyncio.gather(
            *[
                service(index).reserve(runs[index]["id"], fixed_quote(), timeout_seconds=30)
                for index in indices
            ],
            return_exceptions=True,
        )
        accepted = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        assert len(accepted) == count
        assert all(isinstance(r, DomainError) and r.code == code for r in failed)
        with admin.connect() as connection:
            assert len(connection.execute(select(BudgetChargeRecord.id)).all()) == count

    execute(
        funded,
        scenario,
        **{"run_concurrency": 20, "owner_concurrency": 20, "global_concurrency": 20, **caps},
    )


@pytest.mark.integration
def test_unknown_timeout_and_expired_slot_never_refund_money(funded):
    async def scenario(service, runs, clock, admin):
        budget = service()
        hold = await budget.reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)
        await budget.reconcile(hold, None)
        clock.advance(31)
        # An UNKNOWN bill releases the provider slot, while all 100 micro-USD remain held.
        with expect_error("BUDGET_EXCEEDED"):
            await service(2).reserve(runs[2]["id"], fixed_quote(), timeout_seconds=30)
        await budget.reconcile(hold, ProviderUsage(0, 0, 40))
        await budget.reconcile(hold, ProviderUsage(0, 0, 40))
        with expect_error("RECONCILIATION_CONFLICT"):
            await budget.reconcile(hold, ProviderUsage(0, 0, 0))
        await service(2).reserve(runs[2]["id"], fixed_quote(), timeout_seconds=30)
        with admin.connect() as connection:
            assert connection.scalar(select(UsageEntryRecord.cost)) == 40

    execute(funded, scenario, global_daily_microusd=150)


@pytest.mark.integration
def test_killed_worker_releases_expired_concurrency_without_refunding(funded):
    async def scenario(service, runs, clock, admin):
        await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)
        clock.advance(31)
        await service(2).reserve(runs[2]["id"], fixed_quote(), timeout_seconds=30)
        with admin.connect() as connection:
            charges = connection.execute(select(BudgetChargeRecord.active, BudgetChargeRecord.cost))
            assert sorted(charges.all(), key=lambda row: row.active) == [
                (False, None),
                (True, None),
            ]
        with expect_error("BUDGET_EXCEEDED"):
            await service(1).reserve(runs[1]["id"], fixed_quote(), timeout_seconds=30)

    execute(funded, scenario, global_daily_microusd=200, global_concurrency=1)


@pytest.mark.integration
def test_account_purge_preserves_known_global_cost_and_uncertain_hold(funded):
    async def scenario(service, runs, clock, admin):
        known = await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)
        await service().reconcile(known, ProviderUsage(0, 0, 30))
        unknown = await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)
        await service().reconcile(unknown, None)
        with admin.begin() as connection:
            connection.execute(delete(AccountRecord).where(AccountRecord.id == identity.OWNER_A))
        with expect_error("BUDGET_EXCEEDED"):
            await service(2).reserve(runs[2]["id"], fixed_quote(), timeout_seconds=30)
        with admin.connect() as connection:
            assert connection.execute(select(BudgetChargeRecord.cost)).all() == [(30,), (None,)]
            assert connection.execute(select(UsageReservationRecord.id)).all() == []
        with expect_error("NOT_FOUND"):
            await service().reconcile(unknown, ProviderUsage(0, 0, 0))

    execute(funded, scenario, global_daily_microusd=200)


@pytest.mark.integration
def test_unknown_hold_carries_across_utc_days_and_settles_on_reconciliation_day(funded):
    async def scenario(service, runs, clock, admin):
        hold = await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)
        await service().reconcile(hold, None)
        clock.advance(86400)
        fresh = jobs.run_values(clock, owner=identity.OWNER_B)
        with admin.begin() as connection:
            connection.execute(insert(RunRecord).values(**fresh))
        with expect_error("BUDGET_EXCEEDED"):
            await service(2).reserve(fresh["id"], fixed_quote(), timeout_seconds=30)
        await service().reconcile(hold, ProviderUsage(0, 0, 30))
        await service(2).reserve(fresh["id"], fixed_quote(), timeout_seconds=30)
        with admin.connect() as connection:
            assert (
                connection.scalar(
                    select(BudgetChargeRecord.settled_at).where(BudgetChargeRecord.id == hold.id)
                )
                == clock.now()
            )

    execute(funded, scenario, global_daily_microusd=150)


@pytest.mark.integration
def test_foreign_run_stale_epoch_cancel_and_budget_tables_fail_closed(funded):
    async def scenario(service, runs, clock, admin):
        with expect_error("NOT_FOUND"):
            await service().reserve(runs[2]["id"], fixed_quote(), timeout_seconds=30)
        with admin.begin() as connection:
            connection.execute(
                text("UPDATE runs SET cancel_requested=true,revision=revision+1 WHERE id=:id"),
                {"id": runs[0]["id"]},
            )
        with expect_error("RUN_UNAVAILABLE"):
            await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)

    execute(funded, scenario)
    with funded[0].begin() as connection:
        connection.execute(
            text("UPDATE accounts SET status='DELETING',deletion_epoch=1 WHERE id=:owner"),
            {"owner": identity.OWNER_A},
        )

    async def stale(service, runs, clock, admin):
        with expect_error("NOT_FOUND"):
            await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)

    execute(funded, stale)
    app = funded[0].url.set(username=funded[1].username, password=funded[1].password)
    engine = create_engine(app)
    try:
        with engine.connect() as connection, pytest.raises(DBAPIError):
            connection.execute(select(BudgetChargeRecord))
    finally:
        engine.dispose()


@pytest.mark.integration
def test_explicit_zero_and_over_ceiling_actual_cost_are_recorded(funded):
    async def scenario(service, runs, clock, admin):
        hold = await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)
        await service().reconcile(hold, ProviderUsage(0, 0, 0))
        hold = await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)
        with expect_error("COST_BOUND_EXCEEDED"):
            await service().reconcile(hold, ProviderUsage(0, 0, 300))
        with admin.connect() as connection:
            assert sorted(connection.execute(select(BudgetChargeRecord.cost)).scalars()) == [0, 300]
        with expect_error("BUDGET_EXCEEDED"):
            await service(2).reserve(runs[2]["id"], fixed_quote(), timeout_seconds=30)

    execute(funded, scenario, global_daily_microusd=300)


@pytest.mark.integration
def test_public_maintenance_charges_only_global_ledger(funded):
    admin, url, clock, runs = funded
    role = "bb_public_budget_" + uuid4().hex
    with admin.begin() as connection:
        connection.execute(
            text(
                f'CREATE ROLE "{role}" LOGIN NOBYPASSRLS NOSUPERUSER '
                "PASSWORD 'synthetic-budget-only-role-password'"
            )
        )
        connection.execute(text(f'GRANT benefitbridge_public_worker TO "{role}"'))

    async def scenario():
        engine = create_async_engine(
            url.set(username=role, password="synthetic-budget-only-role-password")
        )
        budget = BudgetService(
            async_sessionmaker(engine),
            clock,
            limits(run_microusd=0, owner_daily_microusd=0, global_daily_microusd=150),
            actor=None,
        )
        try:
            hold = await budget.reserve(None, fixed_quote(), timeout_seconds=30)
            await budget.reconcile(hold, ProviderUsage(0, 0, 100))
            with expect_error("BUDGET_EXCEEDED"):
                await budget.reserve(None, fixed_quote(), timeout_seconds=30)
            with admin.connect() as connection:
                assert connection.execute(
                    select(
                        UsageReservationRecord.scope,
                        UsageReservationRecord.owner_id,
                        UsageReservationRecord.run_id,
                    )
                ).all() == [("PUBLIC", None, None)]
            with pytest.raises(DBAPIError):
                async with engine.connect() as connection:
                    await connection.execute(select(AccountRecord.display_name))
        finally:
            await engine.dispose()

    try:
        identity.run(scenario())
    finally:
        with admin.begin() as connection:
            connection.execute(text(f'DROP ROLE "{role}"'))


@pytest.mark.integration
def test_upgrade_backfills_existing_billing_and_downgrade_reupgrade(funded):
    from alembic import command
    from alembic.config import Config

    admin, _, clock, runs = funded
    with admin.begin() as connection:
        config = Config(str(identity.ROOT / "alembic.ini"))
        config.attributes["connection"] = connection
        command.downgrade(config, "0004_documents")
        values = jobs.reservation_values(runs[0], clock)
        connection.execute(insert(UsageReservationRecord).values(**values))
        command.upgrade(config, "head")
        assert connection.execute(
            select(BudgetChargeRecord.amount, BudgetChargeRecord.cost, BudgetChargeRecord.active)
        ).all() == [(100000, None, True)]
        connection.execute(delete(AccountRecord).where(AccountRecord.id == identity.OWNER_A))
        assert connection.scalar(select(BudgetChargeRecord.amount)) == 100000


@pytest.mark.integration
def test_retained_orphan_reconciliation_requires_budget_credentials_and_verified_bill(funded):
    saved = []

    async def reserve(service, runs, clock, admin):
        hold = await service().reserve(runs[0]["id"], fixed_quote(), timeout_seconds=30)
        await service().reconcile(hold, None)
        saved.append(hold.id)
        with admin.begin() as connection:
            connection.execute(delete(AccountRecord).where(AccountRecord.id == identity.OWNER_A))

    execute(funded, reserve)
    admin, url, clock, _ = funded
    role = "bb_budget_reconcile_" + uuid4().hex
    with admin.begin() as connection:
        connection.execute(
            text(
                f'CREATE ROLE "{role}" LOGIN NOBYPASSRLS NOSUPERUSER '
                "PASSWORD 'synthetic-budget-only-role-password'"
            )
        )
        connection.execute(text(f'GRANT benefitbridge_budget_admin TO "{role}"'))

    async def reconcile():
        app = create_async_engine(url)
        budget = create_async_engine(
            url.set(username=role, password="synthetic-budget-only-role-password")
        )
        try:
            with pytest.raises(RuntimeError, match="isolated budget-role"):
                await RetainedChargeReconciler(async_sessionmaker(app), clock).reconcile(
                    saved[0], billed_microusd=30
                )
            operation = RetainedChargeReconciler(async_sessionmaker(budget), clock)
            await operation.reconcile(saved[0], billed_microusd=30)
            await operation.reconcile(saved[0], billed_microusd=30)
            with expect_error("RECONCILIATION_CONFLICT"):
                await operation.reconcile(saved[0], billed_microusd=0)
            with pytest.raises(DBAPIError):
                async with budget.connect() as connection:
                    await connection.execute(select(RunRecord.id))
            with admin.connect() as connection:
                assert connection.scalar(select(BudgetChargeRecord.cost)) == 30
        finally:
            await app.dispose()
            await budget.dispose()

    try:
        identity.run(reconcile())
    finally:
        with admin.begin() as connection:
            connection.execute(text(f'DROP ROLE "{role}"'))


def limits(**changes):
    return BudgetLimits.model_validate(
        {
            "run_microusd": 500000,
            "owner_daily_microusd": 2000000,
            "global_daily_microusd": 10000000,
            "run_concurrency": 1,
            "owner_concurrency": 2,
            "global_concurrency": 2,
            **changes,
        }
    )


def test_quote_reserves_configured_maximum_output_and_ceilings_decimal_prices():
    current = registry(model())
    quote = quote_model_call(current, ModelRole.REASON, input_token_limit=101)
    assert quote.output_token_limit == 128
    assert quote.maximum_microusd == 8
    assert quote.registry_version == current.config.version
    assert quote.registry_fingerprint == current.fingerprint
    assert quote.model.price_version == "synthetic-price-v1"


def test_explicit_output_bound_uses_the_same_verified_prices():
    quote = quote_model_call(
        registry(model()), ModelRole.REASON, input_token_limit=1, output_token_limit=1
    )
    assert quote.maximum_microusd == 1


def test_fast_fallback_preserves_the_resolved_reason_model():
    current = registry(model())
    quote = quote_model_call(current, ModelRole.FAST, input_token_limit=10)
    assert quote.model.role == ModelRole.REASON
    assert quote.model == current.resolve(ModelRole.FAST)
    with pytest.raises(DomainError):
        quote_model_call(current, ModelRole.DEEP, input_token_limit=10)


@pytest.mark.parametrize(
    "inputs,outputs",
    [(-1, 1), (True, 1), (1.5, 1), (1, False), (1, -1), (1, 129), (4096, 1), (2**31, 0)],
)
def test_invalid_token_bounds_never_produce_a_quote(inputs, outputs):
    with pytest.raises(ValidationError):
        quote_model_call(
            registry(model()),
            ModelRole.REASON,
            input_token_limit=inputs,
            output_token_limit=outputs,
        )


def test_quote_does_not_change_when_registry_is_replaced():
    current = registry(model())
    quote = quote_model_call(current, ModelRole.REASON, input_token_limit=100)
    current.config = registry(model(input_price="10.00")).config
    assert quote.maximum_microusd == 8
    with pytest.raises(ValidationError):
        quote.input_token_limit = 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_microusd", -1),
        ("owner_daily_microusd", True),
        ("global_daily_microusd", 1.5),
        ("global_daily_microusd", 2**63),
        ("run_concurrency", 0),
        ("owner_concurrency", -1),
        ("global_concurrency", True),
    ],
)
def test_limits_reject_invalid_money_and_concurrency(field, value):
    with pytest.raises(ValidationError):
        limits(**{field: value})


def test_funded_global_cap_is_required_and_zero_can_disable_spending():
    with pytest.raises(ValidationError):
        BudgetLimits(
            run_microusd=0,
            owner_daily_microusd=0,
            run_concurrency=1,
            owner_concurrency=2,
            global_concurrency=2,
        )
    assert limits(global_daily_microusd=0).global_daily_microusd == 0
