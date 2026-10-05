"""MS-016 real PostgreSQL lease/recovery boundaries with synthetic handlers."""

import asyncio
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, insert, select, text, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from tests.integration import test_identity as identity
from tests.integration import test_jobs as jobs
from tests.integration import test_sources as sources

from benefitbridge.composition import HandlerBinding
from benefitbridge.db.jobs import JobRecord, OutboxRecord, RunRecord, StageOutputRecord
from benefitbridge.db.profiles import AccountRecord, ProfileRecord, ProfileVersionRecord
from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.dto import ArtifactRef
from benefitbridge.domain.enums import RunStatus
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import ActorContext, JobScope, StageResult, WorkflowRepository
from benefitbridge.workflows.queue import PostgresQueue, PublicInputs
from benefitbridge.workflows.worker import RetryableStageError, Worker

identity_database = identity.database
database = jobs.database
accepted = jobs.accepted
catalog = sources.catalog
ACTOR = ActorContext(identity.OWNER_A, 0, "synthetic-queue")
RESULT = StageResult(
    RunStatus.SUCCEEDED, artifact_ref=ArtifactRef(type="evaluation", id=identity.FACT_A)
)


class Inputs(DomainModel):
    pass


class Handler:
    def __init__(self, result=RESULT, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    async def handle(self, context):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


@asynccontextmanager
async def queue_for(database, clock, *, actor=ACTOR, url=None, models=None):
    engine = create_async_engine(url or database[2])
    queue = PostgresQueue(
        async_sessionmaker(engine, expire_on_commit=False),
        clock,
        models or {"discover": Inputs},
        actor=actor,
    )
    try:
        yield queue
    finally:
        await engine.dispose()


def test_dispatch_claim_and_publication_are_idempotent(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            assert isinstance(queue, WorkflowRepository)
            assert await queue.claim(uuid4(), ("discover",)) is None
            assert await queue.dispatch() == 1
            assert await queue.dispatch() == 0
            claim = await queue.claim(uuid4(), ("discover",))
            assert claim.attempt == claim.context.fencing_token == 1
            assert await queue.claim(uuid4(), ("discover",)) is None
            with pytest.raises(DomainError, match="commit before transition"):
                await queue.publish(claim.context, RESULT)
            assert await queue.checkpoint(claim, RESULT)
            assert await queue.checkpoint(claim, RESULT)
            with pytest.raises(DomainError, match="Committed stage differs"):
                await queue.checkpoint(claim, StageResult(RunStatus.SUCCEEDED))
            assert await queue.publish(claim.context, RESULT)
            assert not await queue.publish(claim.context, RESULT)
            run = await queue.get_run(ACTOR, accepted[0]["id"])
            assert run.status == RunStatus.SUCCEEDED
            assert run.result_refs.evaluation_ids == (RESULT.artifact_ref.id,)
            events = await queue.events(ACTOR, run.id, after_seq=-1, limit=100)
            assert [e.seq for e in events] == [0, 1]
            assert [e.message_code for e in events] == ["STAGE_CLAIMED", "STAGE_COMPLETED"]
            assert await queue.events(ACTOR, run.id, after_seq=0, limit=1) == events[1:]

    identity.run(scenario())
    with database[0].connect() as connection:
        assert connection.scalar(select(func.count()).select_from(StageOutputRecord)) == 1


@pytest.mark.parametrize("commit_output", [False, True])
def test_terminated_worker_is_recovered_without_duplicate_artifacts(
    database,
    accepted,
    fake_clock,
    commit_output,
):
    # Termination is a real child-process exit after a committed DB boundary,
    # not a rollback or in-memory fake replacement.
    code = """
import asyncio, os, sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from tests.fakes.providers import FakeClock
from tests.integration.test_queue import ACTOR, Inputs, RESULT
from benefitbridge.workflows.queue import PostgresQueue
from uuid import uuid4
async def crash():
    engine = create_async_engine(os.environ['SYNTHETIC_QUEUE_DSN'])
    queue = PostgresQueue(async_sessionmaker(engine), FakeClock(),
                          {'discover': Inputs}, actor=ACTOR)
    await queue.dispatch()
    claim = await queue.claim(uuid4(), ('discover',))
    assert claim is not None
    if sys.argv[1] == 'commit':
        assert await queue.checkpoint(claim, RESULT)
    os._exit(73)
asyncio.run(crash(), loop_factory=asyncio.SelectorEventLoop)
"""
    env = dict(os.environ, SYNTHETIC_QUEUE_DSN=database[2].render_as_string(hide_password=False))
    process = subprocess.run(
        [sys.executable, "-c", code, "commit" if commit_output else "claim"],
        cwd=identity.ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert process.returncode == 73, process.stderr
    fake_clock.advance(61)

    async def replace():
        async with queue_for(database, fake_clock) as queue:
            handler = Handler()
            assert await Worker(queue, {"discover": HandlerBinding(handler)}).run_once()
            assert handler.calls == (0 if commit_output else 1)
            run = await queue.get_run(ACTOR, accepted[0]["id"])
            assert run.status == RunStatus.SUCCEEDED

    identity.run(replace())
    with database[0].connect() as connection:
        assert connection.scalar(select(func.count()).select_from(StageOutputRecord)) == 1
        assert connection.scalar(select(JobRecord.fencing_token)) == 2


def test_expired_worker_cannot_renew_commit_or_publish(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            first = await queue.claim(uuid4(), ("discover",))
            fake_clock.advance(61)
            second = await queue.claim(uuid4(), ("discover",))
            assert second.context.fencing_token == 2
            assert not await queue.heartbeat(first)
            assert not await queue.checkpoint(first, RESULT)
            assert not await queue.publish(first.context, RESULT)
            assert not await queue.fail(first, "STALE", 1)
            assert await queue.checkpoint(second, RESULT)
            assert await queue.publish(second.context, RESULT)

    identity.run(scenario())


def test_heartbeat_extends_lease_and_blocks_early_reclaim(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            claim = await queue.claim(uuid4(), ("discover",))
            fake_clock.advance(40)
            assert await queue.heartbeat(claim)
            fake_clock.advance(30)
            assert await queue.claim(uuid4(), ("discover",)) is None
            fake_clock.advance(31)
            assert (await queue.claim(uuid4(), ("discover",))).context.fencing_token == 2

    identity.run(scenario())


@pytest.mark.parametrize("commit_output", [False, True])
def test_cancellation_keeps_committed_outputs_without_new_publication(
    database,
    accepted,
    fake_clock,
    commit_output,
):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            claim = await queue.claim(uuid4(), ("discover",))
            if commit_output:
                assert await queue.checkpoint(claim, RESULT)
            assert await queue.cancel(ACTOR, accepted[0]["id"])
            assert not await queue.cancel(ACTOR, accepted[0]["id"])
            assert not await queue.checkpoint(claim, RESULT)
            assert not await queue.publish(claim.context, RESULT)
            run = await queue.get_run(ACTOR, accepted[0]["id"])
            assert run.status == RunStatus.CANCELLED
            assert run.cancel_requested
            assert run.result_refs.evaluation_ids == (
                (RESULT.artifact_ref.id,) if commit_output else ()
            )

    identity.run(scenario())
    with database[0].connect() as connection:
        assert connection.scalar(select(func.count()).select_from(StageOutputRecord)) == int(
            commit_output
        )


def test_worker_cancellation_before_provider_call(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.cancel(ACTOR, accepted[0]["id"])
            handler = Handler()
            assert not await Worker(queue, {"discover": HandlerBinding(handler)}).run_once()
            assert handler.calls == 0
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).status == RunStatus.CANCELLED

    identity.run(scenario())


def test_retries_are_bounded_and_respect_retry_after(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            handler = Handler(error=RetryableStageError("DEPENDENCY_UNAVAILABLE", retry_after=20))
            worker = Worker(queue, {"discover": HandlerBinding(handler)}, jitter=lambda: 0)
            for attempt in range(1, 4):
                assert await worker.run_once()
                assert handler.calls == attempt
                if attempt < 3:
                    assert not await worker.run_once()
                    fake_clock.advance(20)
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).status == RunStatus.FAILED
            assert not await worker.run_once()

    identity.run(scenario())


def test_nonretryable_failure_and_partial_deadline(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            claim = await queue.claim(uuid4(), ("discover",))
            assert await queue.checkpoint(claim, RESULT)
            fake_clock.advance(1801)
            assert await queue.claim(uuid4(), ("discover",)) is None
            run = await queue.get_run(ACTOR, accepted[0]["id"])
            assert run.status == RunStatus.PARTIAL
            assert run.failure_code == "DEADLINE_EXCEEDED"

    identity.run(scenario())


def test_checkpoint_on_last_attempt_recovers_without_fourth_call(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            for _ in range(3):
                claim = await queue.claim(uuid4(), ("discover",))
                if claim.attempt < 3:
                    assert await queue.fail(claim, "RETRY", 1)
                    fake_clock.advance(1)
            assert await queue.checkpoint(claim, RESULT)
            fake_clock.advance(61)
            handler = Handler()
            assert await Worker(queue, {"discover": HandlerBinding(handler)}).run_once()
            assert handler.calls == 0
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).status == RunStatus.SUCCEEDED

    identity.run(scenario())


def test_graph_transition_queues_exactly_one_following_stage(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(
            database, fake_clock, models={"discover": Inputs, "finish": Inputs}
        ) as queue:
            handlers = {
                "discover": HandlerBinding(Handler(StageResult(RunStatus.RUNNING, "finish"))),
                "finish": HandlerBinding(Handler()),
            }
            worker = Worker(queue, handlers)
            assert await worker.run_once()
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).stage == "finish"
            assert await worker.run_once()
            assert not await worker.run_once()
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).status == RunStatus.SUCCEEDED

    identity.run(scenario())
    with database[0].connect() as connection:
        assert connection.scalar(select(func.count()).select_from(JobRecord)) == 2


def test_foreign_owner_and_deletion_epoch_are_fenced(database, accepted, fake_clock):
    async def scenario():
        other = ActorContext(identity.OWNER_B, 0, "other")
        async with queue_for(database, fake_clock, actor=other) as queue:
            assert await queue.dispatch() == 0
            assert await queue.claim(uuid4(), ("discover",)) is None
            assert await queue.get_run(other, accepted[0]["id"]) is None
            with pytest.raises(DomainError, match="unavailable"):
                await queue.events(other, accepted[0]["id"], after_seq=-1, limit=10)
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            claim = await queue.claim(uuid4(), ("discover",))
            with database[0].begin() as connection:
                connection.execute(
                    update(AccountRecord)
                    .where(AccountRecord.id == ACTOR.owner_id)
                    .values(status="DELETING", deletion_epoch=1)
                )
            with pytest.raises(DomainError, match="unavailable"):
                await queue.checkpoint(claim, RESULT)

    identity.run(scenario())


def test_public_role_cannot_receive_private_inputs_and_recovers_checkpoint(
    database, catalog, fake_clock
):
    role = "bb_queue_public_" + uuid4().hex
    role_password = "synthetic-ms016-public-role-password"
    job_id = uuid4()
    with database[0].begin() as connection:
        connection.execute(
            text(f"CREATE ROLE \"{role}\" LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '{role_password}'")
        )
        connection.execute(text(f'GRANT benefitbridge_public_worker TO "{role}"'))
        connection.execute(
            insert(JobRecord).values(
                id=job_id,
                scope="PUBLIC",
                source_id=catalog[2],
                stage="refresh",
                stage_key=str(job_id),
                status="QUEUED",
                due_at=fake_clock.now(),
                deadline_at=fake_clock.now() + timedelta(minutes=30),
                created_at=fake_clock.now(),
            )
        )
        connection.execute(
            insert(OutboxRecord).values(
                id=uuid4(),
                scope="PUBLIC",
                event_key=str(job_id),
                event_type="JOB_READY",
                payload={"job_id": str(job_id)},
                status="PENDING",
                created_at=fake_clock.now(),
            )
        )

    async def scenario():
        url = database[2].set(username=role, password=role_password)
        async with queue_for(database, fake_clock, actor=None, url=url) as queue:
            await queue.dispatch()
            claim = await queue.claim(uuid4(), ("refresh",))
            assert isinstance(claim.context.inputs, PublicInputs)
            assert claim.context.actor is None and claim.context.run_id is None
            assert claim.context.inputs.source_id == catalog[2]
            with pytest.raises(DomainError, match="Public maintenance"):
                await queue.checkpoint(claim, RESULT)
            result = StageResult(RunStatus.SUCCEEDED)
            assert await queue.checkpoint(claim, result)
            fake_clock.advance(61)
            handler = Handler(result)
            assert await Worker(
                queue, {"refresh": HandlerBinding(handler, JobScope.PUBLIC)}
            ).run_once()
            assert handler.calls == 0
        async with queue_for(database, fake_clock, actor=None) as queue:
            with pytest.raises(RuntimeError, match="separate constrained"):
                await queue.dispatch()

    try:
        identity.run(scenario())
    finally:
        with database[0].begin() as connection:
            connection.execute(text(f'DROP ROLE "{role}"'))


def test_skip_locked_claim_skips_a_locked_job(database, accepted, fake_clock):
    with database[0].begin() as connection:
        second_run, second_job = jobs.accept(connection, fake_clock)

    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            with database[0].begin() as locked:
                locked.execute(
                    select(JobRecord.id).where(JobRecord.id == accepted[1]["id"]).with_for_update()
                )
                claim = await asyncio.wait_for(queue.claim(uuid4(), ("discover",)), timeout=2)
                assert claim.context.job_id == second_job["id"]

    identity.run(scenario())


def test_two_connections_claim_only_once(database, accepted, fake_clock):
    async def scenario():
        async with (
            queue_for(database, fake_clock) as first,
            queue_for(database, fake_clock) as second,
        ):
            await first.dispatch()
            claims = await asyncio.gather(
                first.claim(uuid4(), ("discover",)), second.claim(uuid4(), ("discover",))
            )
            assert sum(claim is not None for claim in claims) == 1

    identity.run(scenario())


def test_provider_execution_has_no_open_database_transaction(database, accepted, fake_clock):
    class Probe(Handler):
        async def handle(self, context):
            with database[0].connect() as connection:
                assert (
                    connection.scalar(
                        text(
                            "SELECT count(*) FROM pg_stat_activity "
                            "WHERE datname = current_database() "
                            "AND usename = :app AND state = 'idle in transaction'"
                        ),
                        {"app": database[2].username},
                    )
                    == 0
                )
            return await super().handle(context)

    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            assert await Worker(queue, {"discover": HandlerBinding(Probe())}).run_once()

    identity.run(scenario())


def test_cancel_during_provider_call_stops_at_heartbeat(database, accepted, fake_clock):
    class Inflight(Handler):
        async def handle(self, context):
            started.set()
            await asyncio.Event().wait()

    async def scenario():
        nonlocal started
        started = asyncio.Event()
        async with queue_for(database, fake_clock) as queue:
            worker = Worker(queue, {"discover": HandlerBinding(Inflight())}, heartbeat_seconds=0.01)
            task = asyncio.create_task(worker.run_once())
            await started.wait()
            await queue.cancel(ACTOR, accepted[0]["id"])
            assert await asyncio.wait_for(task, 2)
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).status == RunStatus.CANCELLED

    started = None
    identity.run(scenario())


@pytest.mark.parametrize("checkpoint_first", [False, True])
def test_changed_pinned_profile_prevents_publication(database, fake_clock, checkpoint_first):
    run_values = jobs.run_values(fake_clock, profile_version_id=identity.VERSION_A)
    job_values = jobs.job_values(run_values, fake_clock)
    accepted = (run_values, job_values)
    with database[0].begin() as connection:
        connection.execute(insert(RunRecord).values(**run_values))
        connection.execute(insert(JobRecord).values(**job_values))
        connection.execute(
            insert(OutboxRecord).values(
                id=uuid4(),
                scope="PRIVATE",
                owner_id=ACTOR.owner_id,
                run_id=run_values["id"],
                event_key="accepted",
                event_type="JOB_READY",
                payload={"job_id": str(job_values["id"])},
                status="PENDING",
                created_at=fake_clock.now(),
            )
        )

    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            claim = await queue.claim(uuid4(), ("discover",))
            if checkpoint_first:
                assert await queue.checkpoint(claim, RESULT)
            with database[0].begin() as connection:
                version = uuid4()
                connection.execute(
                    insert(ProfileVersionRecord).values(
                        id=version,
                        owner_id=ACTOR.owner_id,
                        version_number=2,
                        created_at=fake_clock.now(),
                    )
                )
                connection.execute(
                    update(ProfileRecord)
                    .where(ProfileRecord.owner_id == ACTOR.owner_id)
                    .values(current_version_id=version)
                )
            if checkpoint_first:
                assert not await queue.publish(claim.context, RESULT)
            else:
                assert not await queue.checkpoint(claim, RESULT)
            run = await queue.get_run(ACTOR, accepted[0]["id"])
            assert run.failure_code == "VERSION_CONFLICT"
            assert run.result_refs.evaluation_ids == (
                (RESULT.artifact_ref.id,) if checkpoint_first else ()
            )

    identity.run(scenario())


def test_event_cursor_expires_after_24_hours(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            assert await Worker(queue, {"discover": HandlerBinding(Handler())}).run_once()
            fake_clock.advance(86401)
            assert await queue.events(ACTOR, accepted[0]["id"], after_seq=-1, limit=100) == ()
            with pytest.raises(DomainError) as error:
                await queue.events(ACTOR, accepted[0]["id"], after_seq=0, limit=100)
            assert error.value.code == "EVENT_CURSOR_EXPIRED" and error.value.status == 410

    identity.run(scenario())


def test_corrupt_stage_inputs_fail_without_provider_call(database, accepted, fake_clock):
    class RequiredInputs(DomainModel):
        required: str

    async def scenario():
        async with queue_for(database, fake_clock, models={"discover": RequiredInputs}) as queue:
            handler = Handler()
            assert not await Worker(queue, {"discover": HandlerBinding(handler)}).run_once()
            assert handler.calls == 0
            assert (
                await queue.get_run(ACTOR, accepted[0]["id"])
            ).failure_code == "INVALID_STAGE_INPUT"

    identity.run(scenario())


@pytest.mark.parametrize("retryable", [False, True])
def test_nonretryable_or_overlong_retry_after_fails_immediately(
    database, accepted, fake_clock, retryable
):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            error = (
                RetryableStageError("RATE_LIMITED", retry_after=1801)
                if retryable
                else DomainError("UNSAFE_URL", "Unsafe source", 422)
            )
            handler = Handler(error=error)
            worker = Worker(queue, {"discover": HandlerBinding(handler)})
            assert await worker.run_once()
            assert not await worker.run_once()
            assert handler.calls == 1
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).status == RunStatus.FAILED

    identity.run(scenario())


def test_hung_stage_deadline_is_terminal_without_another_poll(database, fake_clock):
    values = jobs.run_values(fake_clock, deadline_at=fake_clock.now() + timedelta(seconds=0.05))
    # The run deadline is authoritative even if a job has a longer deadline.
    job = jobs.job_values(values, fake_clock)
    with database[0].begin() as connection:
        connection.execute(insert(RunRecord).values(**values))
        connection.execute(insert(JobRecord).values(**job))
        connection.execute(
            insert(OutboxRecord).values(
                id=uuid4(),
                scope="PRIVATE",
                owner_id=ACTOR.owner_id,
                run_id=values["id"],
                event_key="accepted",
                event_type="JOB_READY",
                payload={"job_id": str(job["id"])},
                status="PENDING",
                created_at=fake_clock.now(),
            )
        )

    class Hung(Handler):
        async def handle(self, context):
            fake_clock.advance(0.05)
            await asyncio.Event().wait()

    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            worker = Worker(queue, {"discover": HandlerBinding(Hung())})
            assert await asyncio.wait_for(worker.run_once(), 2)
            run = await queue.get_run(ACTOR, values["id"])
            assert run.status == RunStatus.FAILED and run.failure_code == "DEADLINE_EXCEEDED"

    identity.run(scenario())


def test_external_task_cancellation_leaves_a_recoverable_lease(database, accepted, fake_clock):
    class Interrupted(Handler):
        async def handle(self, context):
            entered.set()
            await asyncio.Event().wait()

    async def scenario():
        nonlocal entered
        entered = asyncio.Event()
        async with queue_for(database, fake_clock) as queue:
            task = asyncio.create_task(
                Worker(queue, {"discover": HandlerBinding(Interrupted())}).run_once()
            )
            await entered.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).status == RunStatus.RUNNING
            fake_clock.advance(61)
            assert await Worker(queue, {"discover": HandlerBinding(Handler())}).run_once()
            assert (await queue.get_run(ACTOR, accepted[0]["id"])).status == RunStatus.SUCCEEDED

    entered = None
    identity.run(scenario())


def test_normal_queue_does_not_apply_inference_retry_policy_to_account_purge(database, fake_clock):
    values = jobs.run_values(fake_clock, kind="ACCOUNT_DELETE")
    job = jobs.job_values(values, fake_clock)
    with database[0].begin() as connection:
        connection.execute(insert(RunRecord).values(**values))
        connection.execute(insert(JobRecord).values(**job))
        connection.execute(
            insert(OutboxRecord).values(
                id=uuid4(),
                scope="PRIVATE",
                owner_id=ACTOR.owner_id,
                run_id=values["id"],
                event_key="accepted",
                event_type="JOB_READY",
                payload={"job_id": str(job["id"])},
                status="PENDING",
                created_at=fake_clock.now(),
            )
        )

    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            handler = Handler()
            assert not await Worker(queue, {"discover": HandlerBinding(handler)}).run_once()
            assert handler.calls == 0

    identity.run(scenario())


def test_invalid_handler_transition_is_nonretryable(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            handler = Handler(StageResult(RunStatus.RUNNING, "unregistered"))
            worker = Worker(queue, {"discover": HandlerBinding(handler)})
            assert await worker.run_once()
            assert not await worker.run_once()
            assert handler.calls == 1
            run = await queue.get_run(ACTOR, accepted[0]["id"])
            assert run.status == RunStatus.FAILED and run.failure_code == "INVALID_RUN_STATE"

    identity.run(scenario())


def test_verified_owner_can_reconnect_with_a_different_request_id(database, accepted, fake_clock):
    async def scenario():
        async with queue_for(database, fake_clock) as queue:
            await queue.dispatch()
            await queue.claim(uuid4(), ("discover",))
            reconnected = ActorContext(ACTOR.owner_id, ACTOR.deletion_epoch, "new-request")
            assert await queue.get_run(reconnected, accepted[0]["id"]) is not None
            assert (
                len(await queue.events(reconnected, accepted[0]["id"], after_seq=-1, limit=10)) == 1
            )
            assert await queue.cancel(reconnected, accepted[0]["id"])

    identity.run(scenario())
