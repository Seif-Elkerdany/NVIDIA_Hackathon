"""MS-015 atomic acceptance, tenant isolation, maintenance scopes and replay custody."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import insert, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from tests.fakes.providers import FakeClock
from tests.integration import test_identity as identity
from tests.integration import test_sources as source_fixtures

from benefitbridge.db.jobs import (
    DeletionReceiptRecord,
    IdempotencyRecord,
    JobRecord,
    OutboxRecord,
    ReplayIdentity,
    RunEventRecord,
    RunRecord,
    StageOutputRecord,
    UsageEntryRecord,
    UsageReservationRecord,
    decrypt_replay,
    encrypt_replay,
)
from benefitbridge.domain.dto import (
    ArtifactRef,
    DeletionAccepted,
    RunEvent,
    RunFunnel,
    RunProgress,
    RunReceipt,
    RunResultRefs,
)

identity_database = identity.database
catalog = source_fixtures.catalog


@pytest.fixture
def database(identity_database):
    try:
        yield identity_database
    finally:
        identity_database[1].dispose()


def run_values(clock, owner=identity.OWNER_A, **changes):
    return {
        "id": uuid4(),
        "owner_id": owner,
        "kind": "DISCOVERY",
        "status": "QUEUED",
        "inputs": {},
        "stage": "discover",
        "deletion_epoch": 0,
        "deadline_at": clock.now() + timedelta(minutes=30),
        "created_at": clock.now(),
        "updated_at": clock.now(),
        **changes,
    }


def job_values(run, clock, **changes):
    return {
        "id": uuid4(),
        "scope": "PRIVATE",
        "owner_id": run["owner_id"],
        "run_id": run["id"],
        "stage": "discover",
        "stage_key": "discover-v1",
        "status": "QUEUED",
        "due_at": clock.now(),
        "deadline_at": clock.now() + timedelta(minutes=30),
        "created_at": clock.now(),
        **changes,
    }


def accept(connection, clock, owner=identity.OWNER_A):
    run = run_values(clock, owner)
    connection.execute(insert(RunRecord).values(**run))
    job = job_values(run, clock)
    connection.execute(insert(JobRecord).values(**job))
    connection.execute(
        insert(OutboxRecord).values(
            id=uuid4(),
            scope="PRIVATE",
            owner_id=owner,
            run_id=run["id"],
            event_key="accepted",
            event_type="JOB_READY",
            payload={"job_id": str(job["id"])},
            status="PENDING",
            created_at=clock.now(),
        )
    )
    return run, job


@pytest.fixture
def accepted(database, fake_clock):
    with database[0].begin() as connection:
        run, job = accept(connection, fake_clock)
    return run, job


def test_rollback_leaves_no_run_job_or_orphan_outbox(database, fake_clock):
    _, app, _, _ = database
    with pytest.raises(RuntimeError, match="synthetic transaction failure"):
        with app.begin() as connection:
            identity.context(connection)
            accept(connection, fake_clock)
            raise RuntimeError("synthetic transaction failure")
    with app.begin() as connection:
        identity.context(connection)
        for table in (RunRecord, JobRecord, OutboxRecord):
            assert connection.execute(select(table.id)).all() == []
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(
                insert(OutboxRecord).values(
                    id=uuid4(),
                    scope="PRIVATE",
                    owner_id=identity.OWNER_A,
                    run_id=uuid4(),
                    event_key="orphan",
                    event_type="JOB_READY",
                    payload={},
                    status="PENDING",
                    created_at=fake_clock.now(),
                )
            )


def test_committed_acceptance_is_durable_and_stage_unique(database, accepted, fake_clock):
    run, _ = accepted
    with database[0].connect() as connection:
        assert connection.scalar(select(RunRecord.id)) == run["id"]
        assert connection.scalar(select(OutboxRecord.run_id)) == run["id"]
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(insert(JobRecord).values(**job_values(run, fake_clock)))


def test_run_summary_preserves_shared_types_and_unknown_total(database, accepted):
    with Session(database[0]) as session:
        run = session.get(RunRecord, accepted[0]["id"])
        assert isinstance(run.progress, RunProgress)
        assert run.progress.completed_units == 0 and run.progress.total_units is None
        assert isinstance(run.funnel, RunFunnel)
        assert isinstance(run.result_refs, RunResultRefs)
        assert run.result_refs.opportunity_ids == ()
        assert run.warnings == [] and run.failure_code is None


def test_concurrent_stage_enqueue_has_one_winner(database, accepted, fake_clock):
    barrier = Barrier(2)

    def enqueue():
        barrier.wait(timeout=10)
        try:
            with database[0].begin() as connection:
                connection.execute(
                    insert(JobRecord).values(
                        **job_values(accepted[0], fake_clock, stage_key="next-stage-v1")
                    )
                )
            return "committed"
        except IntegrityError:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: enqueue(), range(2)))
    assert sorted(results) == ["committed", "duplicate"]


def test_event_order_and_single_stage_output(database, accepted, fake_clock):
    run, job = accepted
    artifact = ArtifactRef(type="opportunity", id=uuid4())
    with database[0].begin() as connection:
        for seq in (2, 0, 1):
            connection.execute(
                insert(RunEventRecord).values(
                    owner_id=run["owner_id"],
                    run_id=run["id"],
                    seq=seq,
                    event_type="STATE",
                    at=fake_clock.now(),
                    payload=RunEvent(
                        run_id=run["id"],
                        seq=seq,
                        stage="discover",
                        status="QUEUED",
                        message_code="ACCEPTED",
                        artifact_ref=None,
                        at=fake_clock.now(),
                    ),
                )
            )
        connection.execute(
            insert(StageOutputRecord).values(
                owner_id=run["owner_id"],
                run_id=run["id"],
                job_id=job["id"],
                stage_key=job["stage_key"],
                fencing_token=1,
                artifact_ref=artifact,
                created_at=fake_clock.now(),
            )
        )
    with database[0].connect() as connection:
        assert list(
            connection.execute(select(RunEventRecord.seq).order_by(RunEventRecord.seq)).scalars()
        ) == [0, 1, 2]
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(
                insert(StageOutputRecord).values(
                    owner_id=run["owner_id"],
                    run_id=run["id"],
                    job_id=job["id"],
                    stage_key=job["stage_key"],
                    fencing_token=2,
                    artifact_ref=artifact,
                    created_at=fake_clock.now(),
                )
            )


@pytest.mark.parametrize("table", ["job", "outbox", "event", "reservation"])
def test_cross_owner_run_reference_fails(database, accepted, fake_clock, table):
    run, _ = accepted
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            if table == "job":
                connection.execute(
                    insert(JobRecord).values(
                        **job_values(
                            run, fake_clock, owner_id=identity.OWNER_B, stage_key="wrong-owner"
                        )
                    )
                )
            elif table == "outbox":
                connection.execute(
                    insert(OutboxRecord).values(
                        id=uuid4(),
                        scope="PRIVATE",
                        owner_id=identity.OWNER_B,
                        run_id=run["id"],
                        event_key="wrong-owner",
                        event_type="JOB_READY",
                        payload={},
                        status="PENDING",
                        created_at=fake_clock.now(),
                    )
                )
            elif table == "event":
                connection.execute(
                    insert(RunEventRecord).values(
                        owner_id=identity.OWNER_B,
                        run_id=run["id"],
                        seq=0,
                        event_type="STATE",
                        at=fake_clock.now(),
                        payload=RunEvent(
                            run_id=run["id"],
                            seq=0,
                            stage="discover",
                            status="QUEUED",
                            message_code="ACCEPTED",
                            artifact_ref=None,
                            at=fake_clock.now(),
                        ),
                    )
                )
            else:
                connection.execute(
                    insert(UsageReservationRecord).values(
                        **reservation_values(run, fake_clock, owner_id=identity.OWNER_B)
                    )
                )


def test_rls_hides_other_owner_and_tombstoned_runs(database, accepted):
    _, app, _, _ = database
    with app.begin() as connection:
        identity.context(connection, identity.OWNER_B)
        for table in (RunRecord, JobRecord, OutboxRecord):
            assert connection.execute(select(table.id)).all() == []

    with app.begin() as connection:
        assert connection.execute(select(RunRecord.id)).all() == []
    with database[0].begin() as connection:
        connection.execute(
            text("UPDATE accounts SET status='DELETING', deletion_epoch=1 WHERE id=:owner"),
            {"owner": identity.OWNER_A},
        )
    with app.begin() as connection:
        identity.context(connection)
        for table in (RunRecord, JobRecord, OutboxRecord):
            assert connection.execute(select(table.id)).all() == []


def test_private_job_requires_visible_current_epoch_run(database, fake_clock):
    run = run_values(fake_clock, deletion_epoch=1)
    with database[0].begin() as connection:
        connection.execute(insert(RunRecord).values(**run))
    with database[1].begin() as connection:
        identity.context(connection)
        with pytest.raises(DBAPIError):
            with connection.begin_nested():
                connection.execute(insert(JobRecord).values(**job_values(run, fake_clock)))


def test_run_inputs_and_outbox_payload_are_immutable(database, accepted):
    for statement in (
        "UPDATE runs SET inputs=jsonb_build_object('changed',true), revision=revision+1",
        "UPDATE runs SET deletion_epoch=1, revision=revision+1",
        "UPDATE outbox SET payload=jsonb_build_object('changed',true), revision=revision+1",
    ):
        with pytest.raises(IntegrityError):
            with database[0].begin() as connection:
                connection.execute(text(statement))


def test_profile_version_reference_is_owner_consistent(database, fake_clock):
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(
                insert(RunRecord).values(
                    **run_values(fake_clock, profile_version_id=identity.VERSION_B)
                )
            )


def test_public_maintenance_cannot_carry_owner_or_run(catalog, accepted, fake_clock):
    engine, _, source, _, _, _ = catalog
    run, _ = accepted
    for changes in (
        {"owner_id": run["owner_id"], "run_id": None},
        {"owner_id": None, "run_id": run["id"]},
    ):
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    insert(JobRecord).values(
                        **job_values(
                            run,
                            fake_clock,
                            scope="PUBLIC",
                            source_id=source,
                            stage_key=uuid4().hex,
                            **changes,
                        )
                    )
                )
    with engine.begin() as connection:
        connection.execute(text("SET LOCAL ROLE benefitbridge_public_worker"))
        public_job = job_values(
            run,
            fake_clock,
            scope="PUBLIC",
            owner_id=None,
            run_id=None,
            source_id=source,
            stage_key="public-source-refresh",
        )
        connection.execute(insert(JobRecord).values(**public_job))
        assert connection.execute(select(JobRecord.id)).scalars().all() == [public_job["id"]]
        with pytest.raises(DBAPIError):
            with connection.begin_nested():
                connection.execute(select(RunRecord.id))
        connection.execute(
            insert(OutboxRecord).values(
                id=uuid4(),
                scope="PUBLIC",
                event_key="public-source-refresh",
                event_type="REFRESH",
                payload={"job_id": str(public_job["id"])},
                status="PENDING",
                created_at=fake_clock.now(),
            )
        )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"prompt": "private fixture content"},
        {"owner_id": str(identity.OWNER_A)},
        {"source_id": str(uuid4())},
    ],
)
def test_public_payload_allowlist(catalog, fake_clock, payload):
    with pytest.raises(IntegrityError):
        with catalog[0].begin() as connection:
            connection.execute(
                insert(OutboxRecord).values(
                    id=uuid4(),
                    scope="PUBLIC",
                    event_key=uuid4().hex,
                    event_type="REFRESH",
                    payload=payload,
                    status="PENDING",
                    created_at=fake_clock.now(),
                )
            )


def test_lease_counter_and_fence_constraints(database, accepted, fake_clock):
    _, job = accepted
    worker = uuid4()
    with database[0].begin() as connection:
        connection.execute(
            text("""UPDATE jobs SET status='RUNNING', attempt=1, fencing_token=1,
            lease_owner=:worker, lease_until=:until, revision=revision+1 WHERE id=:job"""),
            {"worker": worker, "until": fake_clock.now() + timedelta(seconds=60), "job": job["id"]},
        )
    for statement in (
        "UPDATE jobs SET fencing_token=0, revision=revision+1 WHERE id=:job",
        "UPDATE jobs SET attempt=4, revision=revision+1 WHERE id=:job",
        "UPDATE jobs SET stage_key='different', revision=revision+1 WHERE id=:job",
        "UPDATE jobs SET lease_owner=NULL, revision=revision+1 WHERE id=:job",
    ):
        with pytest.raises(IntegrityError):
            with database[0].begin() as connection:
                connection.execute(text(statement), {"job": job["id"]})


def replay_values(owner, clock, key="synthetic-key-0001"):
    run = uuid4()
    identity_key = ReplayIdentity(owner, "start_discovery", key, "a" * 64)
    receipt = RunReceipt(
        run_id=run,
        status="QUEUED",
        status_url=f"/api/v1/runs/{run}",
        events_url=f"/api/v1/runs/{run}/events",
    )
    return {
        "owner_id": owner,
        "operation": identity_key.operation,
        "key": key,
        "request_hash": identity_key.request_hash,
        "response_ciphertext": encrypt_replay(receipt, identity_key, encryption_key=b"s" * 32),
        "response_status": 202,
        "created_at": clock.now(),
        "expires_at": clock.now() + timedelta(hours=24),
    }


def test_idempotency_scoped_uniqueness_and_plaintext_rejection(database, fake_clock):
    values = replay_values(identity.OWNER_A, fake_clock)
    with database[0].begin() as connection:
        connection.execute(insert(IdempotencyRecord).values(**values))
        connection.execute(
            insert(IdempotencyRecord).values(**replay_values(identity.OWNER_B, fake_clock))
        )
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(insert(IdempotencyRecord).values(**values))
    values = replay_values(identity.OWNER_A, fake_clock, "another-key-00001")
    values["response_ciphertext"] = b'{"receipt_token":"synthetic-secret"}'
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(insert(IdempotencyRecord).values(**values))


def reservation_values(run, clock, **changes):
    return {
        "id": uuid4(),
        "scope": "PRIVATE",
        "owner_id": run["owner_id"],
        "run_id": run["id"],
        "amount": 100_000,
        "status": "RESERVED",
        "registry_version": "synthetic-v1",
        "price_version": "synthetic-v1",
        "created_at": clock.now(),
        "expires_at": clock.now() + timedelta(hours=1),
        **changes,
    }


def test_public_usage_is_global_and_unknown_is_not_free(database, accepted, fake_clock):
    run, _ = accepted
    reservation = reservation_values(run, fake_clock, scope="PUBLIC", owner_id=None, run_id=None)
    with database[0].begin() as connection:
        connection.execute(text("SET LOCAL ROLE benefitbridge_budget_admin"))
        connection.execute(insert(UsageReservationRecord).values(**reservation))
        connection.execute(
            insert(UsageEntryRecord).values(
                id=uuid4(),
                scope="PUBLIC",
                reservation_id=reservation["id"],
                provider_usage={},
                cost=None,
                status="UNKNOWN",
                registry_version="synthetic-v1",
                price_version="synthetic-v1",
                created_at=fake_clock.now(),
            )
        )
        with pytest.raises(DBAPIError):
            with connection.begin_nested():
                connection.execute(select(RunRecord.id))
    with database[0].connect() as connection:
        entry = connection.execute(
            select(UsageEntryRecord.owner_id, UsageEntryRecord.run_id, UsageEntryRecord.cost)
        ).one()
        assert entry == (None, None, None)
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(
                insert(UsageEntryRecord).values(
                    id=uuid4(),
                    scope="PUBLIC",
                    reservation_id=reservation["id"],
                    provider_usage={},
                    cost=0,
                    status="UNKNOWN",
                    registry_version="synthetic-v1",
                    price_version="synthetic-v1",
                    created_at=fake_clock.now(),
                )
            )


def test_usage_cannot_change_reservation_scope_or_owner(database, accepted, fake_clock):
    run, _ = accepted
    reservation = reservation_values(run, fake_clock)
    with database[0].begin() as connection:
        connection.execute(insert(UsageReservationRecord).values(**reservation))
    for changes in (
        {"scope": "PUBLIC", "owner_id": None, "run_id": None},
        {"scope": "PRIVATE", "owner_id": identity.OWNER_B, "run_id": run["id"]},
    ):
        with pytest.raises(IntegrityError):
            with database[0].begin() as connection:
                connection.execute(
                    insert(UsageEntryRecord).values(
                        id=uuid4(),
                        reservation_id=reservation["id"],
                        provider_usage={},
                        cost=0,
                        status="KNOWN",
                        registry_version="synthetic-v1",
                        price_version="synthetic-v1",
                        created_at=fake_clock.now(),
                        **changes,
                    )
                )


@pytest.mark.parametrize(
    "changes",
    [
        {"price_version": "different-price"},
        {"registry_version": "different-registry"},
        {"provider_usage": {"input_tokens": -1}},
        {"provider_usage": {"output_tokens": 1.5}},
        {"provider_usage": {"provider_request_id": {"prompt": "private fixture"}}},
    ],
)
def test_usage_provenance_and_scalar_counts(database, accepted, fake_clock, changes):
    run, _ = accepted
    reservation = reservation_values(run, fake_clock)
    with database[0].begin() as connection:
        connection.execute(insert(UsageReservationRecord).values(**reservation))
    values = dict(
        id=uuid4(),
        scope="PRIVATE",
        owner_id=run["owner_id"],
        run_id=run["id"],
        reservation_id=reservation["id"],
        provider_usage={},
        cost=0,
        status="KNOWN",
        registry_version="synthetic-v1",
        price_version="synthetic-v1",
        created_at=fake_clock.now(),
    )
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(insert(UsageEntryRecord).values(**{**values, **changes}))


def test_receipts_deny_ordinary_access_and_survive_account_purge(database, fake_clock):
    admin, app, _, _ = database
    receipt = uuid4()
    with admin.begin() as connection:
        connection.execute(
            insert(DeletionReceiptRecord).values(
                id=receipt,
                token_hash=b"h" * 32,
                status="PENDING",
                requested_at=fake_clock.now(),
                expires_at=fake_clock.now() + timedelta(days=7),
            )
        )
        connection.execute(text("SET LOCAL ROLE benefitbridge_identity_admin"))
        connection.execute(
            text("DELETE FROM accounts WHERE id=:owner"), {"owner": identity.OWNER_A}
        )
    with app.begin() as connection:
        identity.context(connection)
        with pytest.raises(DBAPIError):
            with connection.begin_nested():
                connection.execute(select(DeletionReceiptRecord.id))
    with admin.begin() as connection:
        connection.execute(text("SET LOCAL ROLE benefitbridge_receipt_admin"))
        assert connection.scalar(select(DeletionReceiptRecord.id)) == receipt
        with pytest.raises(DBAPIError):
            with connection.begin_nested():
                connection.execute(select(RunRecord.id))


def test_receipt_ttl_is_seven_utc_days_across_cairo_clock_change(database):
    clock = FakeClock(datetime(2026, 10, 29, 12, tzinfo=UTC))
    with database[0].begin() as connection:
        connection.execute(text("SET LOCAL TIME ZONE 'Africa/Cairo'"))
        connection.execute(
            insert(DeletionReceiptRecord).values(
                id=uuid4(),
                token_hash=b"t" * 32,
                status="PENDING",
                requested_at=clock.now(),
                expires_at=clock.now() + timedelta(days=7),
            )
        )
        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                connection.execute(
                    insert(DeletionReceiptRecord).values(
                        id=uuid4(),
                        token_hash=b"u" * 32,
                        status="PENDING",
                        requested_at=clock.now(),
                        expires_at=clock.now() + timedelta(days=7, hours=1),
                    )
                )


def test_delete_replay_survives_purge_while_ordinary_replay_is_erased(database, fake_clock):
    admin, app, _, _ = database
    context = ReplayIdentity(identity.OWNER_A, "delete_account", "synthetic-key-0001", "a" * 64)
    receipt = uuid4()
    body = DeletionAccepted(
        receipt_id=receipt,
        receipt_token="synthetic-private-capability",
        receipt_url=f"/api/v1/deletion-receipts/{receipt}",
        status="PENDING",
        expires_at=fake_clock.now() + timedelta(days=7),
    )
    values = {
        **replay_values(identity.OWNER_A, fake_clock),
        "operation": "delete_account",
        "response_ciphertext": encrypt_replay(body, context, encryption_key=b"s" * 32),
    }
    with admin.begin() as connection:
        connection.execute(
            insert(IdempotencyRecord).values(**replay_values(identity.OWNER_A, fake_clock))
        )
        connection.execute(insert(IdempotencyRecord).values(**values))
        connection.execute(text("SET LOCAL ROLE benefitbridge_identity_admin"))
        connection.execute(
            text("DELETE FROM accounts WHERE id=:owner"), {"owner": identity.OWNER_A}
        )
        rows = connection.execute(
            select(IdempotencyRecord.operation, IdempotencyRecord.response_ciphertext)
        ).all()
        assert len(rows) == 1 and rows[0].operation == "delete_account"
        assert (
            DeletionAccepted.model_validate_json(
                decrypt_replay(rows[0].response_ciphertext, context, encryption_key=b"s" * 32)
            )
            == body
        )
    with app.begin() as connection:
        identity.context(connection)
        assert connection.execute(select(IdempotencyRecord.key)).all() == []
    with pytest.raises(IntegrityError):
        with admin.begin() as connection:
            connection.execute(
                insert(IdempotencyRecord).values(
                    **replay_values(identity.OWNER_A, fake_clock, key="new-key-after-purge")
                )
            )


def test_jobs_migration_downgrade_and_reupgrade(database):
    with database[0].begin() as connection:
        config = Config(str(identity.ROOT / "alembic.ini"))
        config.attributes["connection"] = connection
        command.downgrade(config, "0002_sources")
        assert connection.scalar(text("SELECT to_regclass('public.jobs')")) is None
        command.upgrade(config, "head")
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == "0004_documents"
        )
