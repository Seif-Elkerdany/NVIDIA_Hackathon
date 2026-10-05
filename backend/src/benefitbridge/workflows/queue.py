"""Owner-partitioned private queues and separately credentialed public maintenance.

The caller supplies verified ActorContext, never an owner discovered with an
administration credential. Handlers must stage artifacts under stage_key and
must not publish current decisions outside the fenced publication transaction.
Paid handlers retain responsibility for the MS-019 reservation port.
"""

import math
import re
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import String, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from benefitbridge.db.base import owner_transaction
from benefitbridge.db.jobs import (
    JobRecord,
    JobStatus,
    OutboxRecord,
    OutboxStatus,
    RunEventRecord,
    RunRecord,
    StageOutputRecord,
)
from benefitbridge.db.profiles import ProfileRecord
from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.dto import ArtifactRef, Run, RunEvent, RunResultRefs
from benefitbridge.domain.enums import RunKind, RunStatus
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import ActorContext, Clock, JobScope, StageContext, StageResult

LEASE_SECONDS = 60
HEARTBEAT_SECONDS = 15
TERMINAL = {RunStatus.SUCCEEDED, RunStatus.PARTIAL, RunStatus.FAILED, RunStatus.CANCELLED}


class PublicInputs(DomainModel):
    """Public handlers receive identifiers only, never private run inputs."""

    source_id: UUID | None = None
    snapshot_id: UUID | None = None
    opportunity_id: UUID | None = None


class Checkpoint(DomainModel):
    status: RunStatus
    next_stage: str | None = None
    artifact_ref: ArtifactRef | None = None
    warning_codes: tuple[str, ...] = ()

    def result(self) -> StageResult:
        return StageResult(self.status, self.next_stage, self.artifact_ref, self.warning_codes)


@dataclass(frozen=True)
class Claim:
    context: StageContext
    attempt: int
    max_attempts: int
    worker_id: UUID
    checkpoint: StageResult | None = None


def logical_key(previous: str, next_stage: str) -> str:
    return f"{next_stage}:{sha256(previous.encode()).hexdigest()}"


class PostgresQueue:
    """A partition uses either ordinary app credentials + actor, or public-worker credentials.

    Private partitions are scheduled by trusted server composition. This class
    deliberately has no privileged cross-tenant discovery or deletion-purge path.
    Public jobs are independent one-stage maintenance tasks; graph transitions
    and private artifact references are forbidden in that composition.
    """

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        clock: Clock,
        input_models: Mapping[str, type[DomainModel]],
        *,
        actor: ActorContext | None,
    ) -> None:
        self.sessions = sessions
        self.clock = clock
        self.input_models = dict(input_models)
        self.actor = actor
        self.scope = JobScope.PRIVATE if actor else JobScope.PUBLIC

    def _owns(self, actor: ActorContext | None) -> bool:
        if self.actor is None:
            return actor is None
        return actor is not None and (actor.owner_id, actor.deletion_epoch) == (
            self.actor.owner_id,
            self.actor.deletion_epoch,
        )

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        if self.actor is not None:
            async with owner_transaction(self.sessions, self.actor) as session:
                yield session
        else:
            async with self.sessions() as session, session.begin():
                allowed = await session.scalar(
                    text(
                        "SELECT pg_has_role(current_user, 'benefitbridge_public_worker', 'member') "
                        "AND NOT pg_has_role(current_user, 'benefitbridge_app', 'member') "
                        "AND NOT pg_has_role(current_user, "
                        "'benefitbridge_identity_admin', 'member') "
                        "AND NOT rolsuper AND NOT rolbypassrls FROM pg_catalog.pg_roles "
                        "WHERE rolname = current_user"
                    )
                )
                if not allowed:
                    raise RuntimeError("Public work requires separate constrained credentials")
                yield session

    async def _run(self, session: AsyncSession, run_id: UUID | None) -> RunRecord | None:
        if self.actor is None or run_id is None:
            return None
        return (
            await session.execute(
                select(RunRecord)
                .where(
                    RunRecord.id == run_id,
                    RunRecord.owner_id == self.actor.owner_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

    async def _event(
        self, session: AsyncSession, run: RunRecord, code: str, artifact: ArtifactRef | None = None
    ) -> None:
        seq = await session.scalar(
            select(func.max(RunEventRecord.seq)).where(
                RunEventRecord.owner_id == run.owner_id,
                RunEventRecord.run_id == run.id,
            )
        )
        seq = 0 if seq is None else seq + 1
        event = RunEvent(
            run_id=run.id,
            seq=seq,
            stage=run.stage,
            status=run.status,
            message_code=code,
            artifact_ref=artifact,
            at=self.clock.now(),
        )
        session.add(
            RunEventRecord(
                owner_id=run.owner_id,
                run_id=run.id,
                seq=seq,
                event_type=code,
                payload=event,
                at=self.clock.now(),
            )
        )

    def _state(self, run: RunRecord, status: RunStatus, code: str | None = None) -> None:
        run.status = status
        run.failure_code = code
        run.updated_at = self.clock.now()
        run.revision += 1

    def _release(self, job: JobRecord, status: JobStatus) -> None:
        job.status = status
        job.lease_owner = None
        job.lease_until = None
        job.revision += 1

    async def dispatch(self, limit: int = 100) -> int:
        """Acknowledgement and readiness are one transaction; redelivery changes no job."""
        if not 1 <= limit <= 100:
            raise ValueError("Dispatch limit must be 1..100")
        async with self.transaction() as session:
            rows = (
                await session.scalars(
                    select(OutboxRecord)
                    .where(
                        OutboxRecord.scope == self.scope,
                        OutboxRecord.status == OutboxStatus.PENDING,
                        OutboxRecord.event_type == "JOB_READY",
                    )
                    .order_by(OutboxRecord.created_at, OutboxRecord.id)
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
            ).all()
            for row in rows:
                job_id = UUID(str(row.payload["job_id"]))
                job = await session.get(JobRecord, job_id)
                if job is None or job.scope != self.scope or job.run_id != row.run_id:
                    raise DomainError("INVALID_RUN_STATE", "Invalid work delivery", 409)
                row.status = OutboxStatus.DELIVERED
                row.revision += 1
            return len(rows)

    async def _checkpoint(self, session: AsyncSession, job: JobRecord) -> StageResult | None:
        row = await session.scalar(
            select(OutboxRecord).where(
                OutboxRecord.scope == self.scope,
                OutboxRecord.event_key == f"committed:{job.id}",
                OutboxRecord.run_id == job.run_id,
            )
        )
        if row is None:
            return None
        if self.scope == JobScope.PUBLIC:
            artifact = (
                ArtifactRef(type="opportunity", id=UUID(str(row.payload["opportunity_id"])))
                if "opportunity_id" in row.payload
                else None
            )
            return StageResult(RunStatus.SUCCEEDED, artifact_ref=artifact)
        return Checkpoint.model_validate(row.payload).result()

    async def claim(self, worker_id: UUID, stages: tuple[str, ...]) -> Claim | None:
        """SKIP LOCKED plus account-first ordering; expired leases fence old workers."""
        now = self.clock.now()
        async with self.transaction() as session:
            # A delivered outbox is the eligibility gate; inserted but uncommitted
            # acceptances and unacknowledged deliveries cannot become provider work.
            ready = (
                select(OutboxRecord.run_id)
                .where(
                    OutboxRecord.scope == self.scope,
                    OutboxRecord.event_type == "JOB_READY",
                    OutboxRecord.status == OutboxStatus.DELIVERED,
                    OutboxRecord.payload["job_id"].astext == JobRecord.id.cast(String),
                )
                .exists()
            )
            query = (
                select(JobRecord)
                .where(
                    JobRecord.scope == self.scope,
                    JobRecord.stage.in_(stages),
                    ready,
                    or_(
                        (JobRecord.status == JobStatus.QUEUED) & (JobRecord.due_at <= now),
                        (JobRecord.status == JobStatus.RUNNING) & (JobRecord.lease_until <= now),
                    ),
                )
                .order_by(JobRecord.due_at, JobRecord.id)
            )
            if self.actor is not None:
                # Purge is operated with separate permissions and retention-SLO
                # retry policy (MS-064), never the normal inference retry budget.
                query = query.where(
                    select(RunRecord.id)
                    .where(
                        RunRecord.id == JobRecord.run_id,
                        RunRecord.kind != RunKind.ACCOUNT_DELETE,
                    )
                    .exists()
                )
            # Account locking serializes private mutations for this owner. Run
            # locking must precede job locking, consistent with publication.
            run = None
            job = None
            if self.actor is None:
                job = await session.scalar(query.limit(1).with_for_update(skip_locked=True))
            else:
                candidates = (await session.scalars(query.limit(100))).all()
                for candidate in candidates:
                    run = await self._run(session, candidate.run_id)
                    job = await session.scalar(
                        query.where(JobRecord.id == candidate.id).with_for_update(skip_locked=True)
                    )
                    if job is not None:
                        break
            if job is None:
                return None
            checkpoint = await self._checkpoint(session, job)
            if run and (run.cancel_requested or run.status in TERMINAL):
                self._release(job, JobStatus.CANCELLED)
                if run.status not in TERMINAL:
                    self._state(run, RunStatus.CANCELLED)
                    await self._event(session, run, "CANCELLED")
                return None
            if run:
                try:
                    inputs = self.input_models[job.stage].model_validate(run.inputs)
                except ValidationError:
                    self._release(job, JobStatus.FAILED)
                    await self._failed(session, run, "INVALID_STAGE_INPUT")
                    return None
            else:
                inputs = PublicInputs(
                    source_id=job.source_id,
                    snapshot_id=job.snapshot_id,
                    opportunity_id=job.opportunity_id,
                )
            deadline = min(job.deadline_at, run.deadline_at) if run else job.deadline_at
            if deadline <= now or (job.attempt >= min(job.max_attempts, 3) and checkpoint is None):
                self._release(job, JobStatus.FAILED)
                if run:
                    await self._failed(
                        session,
                        run,
                        "DEADLINE_EXCEEDED" if deadline <= now else "ATTEMPTS_EXHAUSTED",
                    )
                return None
            # Recovery of a committed output consumes no new provider attempt.
            # The schema requires a claim increment; give checkpoint recovery a
            # slot without allowing a fourth provider attempt.
            if checkpoint is not None and job.attempt == job.max_attempts:
                job.max_attempts += 1
            job.attempt += 1
            job.fencing_token += 1
            job.revision += 1
            job.status = JobStatus.RUNNING
            job.lease_owner = worker_id
            job.lease_until = min(now + timedelta(seconds=LEASE_SECONDS), deadline)
            if run:
                self._state(run, RunStatus.RUNNING)
                await self._event(session, run, "STAGE_CLAIMED")
            context = StageContext(
                job.id,
                job.run_id,
                run.kind if run else None,
                job.stage,
                job.stage_key,
                self.scope,
                self.actor,
                job.fencing_token,
                deadline.astimezone(UTC),
                inputs,
            )
            return Claim(context, job.attempt, job.max_attempts, worker_id, checkpoint)

    async def _locked(
        self,
        session: AsyncSession,
        context: StageContext,
        worker_id: UUID | None = None,
        *,
        allow_deadline_failure: bool = False,
    ) -> tuple[RunRecord | None, JobRecord | None]:
        if context.scope != self.scope or not self._owns(context.actor):
            return None, None
        run = await self._run(session, context.run_id)
        job = await session.scalar(
            select(JobRecord)
            .where(
                JobRecord.id == context.job_id,
                JobRecord.scope == self.scope,
                JobRecord.run_id == context.run_id,
            )
            .with_for_update()
        )
        if (
            job is None
            or job.status != JobStatus.RUNNING
            or job.fencing_token != context.fencing_token
            or job.stage_key != context.stage_key
            or job.stage != context.stage
            or job.lease_until is None
            or (
                job.lease_until <= self.clock.now()
                and not (
                    allow_deadline_failure
                    and min(job.deadline_at, context.deadline_at) <= self.clock.now()
                )
            )
            or (worker_id is not None and job.lease_owner != worker_id)
        ):
            return run, None
        return run, job

    async def heartbeat(self, claim: Claim) -> bool:
        async with self.transaction() as session:
            run, job = await self._locked(session, claim.context, claim.worker_id)
            if job is None or (run and (run.cancel_requested or run.status in TERMINAL)):
                return False
            job.lease_until = min(
                self.clock.now() + timedelta(seconds=LEASE_SECONDS),
                job.deadline_at,
                claim.context.deadline_at,
            )
            job.revision += 1
            return True

    async def checkpoint(self, claim: Claim, result: StageResult) -> bool:
        """Commit the immutable stage output before any graph transition (R10.04)."""
        self.validate_result(result)
        async with self.transaction() as session:
            run, job = await self._locked(session, claim.context, claim.worker_id)
            if job is None or (run and (run.cancel_requested or run.status in TERMINAL)):
                return False
            if run and run.profile_version_id is not None:
                current = await session.scalar(
                    select(ProfileRecord.current_version_id).where(
                        ProfileRecord.owner_id == run.owner_id
                    )
                )
                if current != run.profile_version_id:
                    self._release(job, JobStatus.FAILED)
                    await self._failed(session, run, "VERSION_CONFLICT")
                    return False
            existing = await self._checkpoint(session, job)
            if existing is not None:
                if existing != result:
                    raise DomainError("INVALID_RUN_STATE", "Committed stage differs", 409)
                return True
            payload: dict[str, object]
            if run:
                payload = Checkpoint(
                    status=result.status,
                    next_stage=result.next_stage,
                    artifact_ref=result.artifact_ref,
                    warning_codes=result.warning_codes,
                ).model_dump(mode="json")
                if result.artifact_ref:
                    session.add(
                        StageOutputRecord(
                            owner_id=run.owner_id,
                            run_id=run.id,
                            stage_key=job.stage_key,
                            job_id=job.id,
                            fencing_token=job.fencing_token,
                            artifact_ref=result.artifact_ref,
                            created_at=self.clock.now(),
                        )
                    )
                    # A completed artifact survives later cancellation/deadline
                    # failure, while the run's graph state still has not advanced.
                    self._append_ref(run, result.artifact_ref)
                    run.revision += 1
                    run.updated_at = self.clock.now()
            else:
                payload = {"job_id": str(job.id)}
                if result.artifact_ref:
                    payload["opportunity_id"] = str(result.artifact_ref.id)
            session.add(
                OutboxRecord(
                    id=uuid4(),
                    scope=self.scope,
                    owner_id=job.owner_id,
                    run_id=job.run_id,
                    event_key=f"committed:{job.id}",
                    event_type="STAGE_COMMITTED",
                    payload=payload,
                    status=OutboxStatus.DELIVERED,
                    created_at=self.clock.now(),
                )
            )
            return True

    def validate_result(self, result: StageResult) -> None:
        if result.status not in TERMINAL | {RunStatus.RUNNING, RunStatus.WAITING_USER}:
            raise DomainError("INVALID_RUN_STATE", "Invalid stage outcome", 409)
        if (
            (result.status == RunStatus.RUNNING) != (result.next_stage is not None)
            or (result.next_stage is not None and result.next_stage not in self.input_models)
            or any(
                re.fullmatch(r"[A-Z][A-Z0-9_]{0,99}", code) is None for code in result.warning_codes
            )
        ):
            raise DomainError("INVALID_RUN_STATE", "Invalid stage transition", 409)
        if self.scope == JobScope.PUBLIC and (
            result.status != RunStatus.SUCCEEDED
            or result.next_stage is not None
            or result.warning_codes
            or (result.artifact_ref and result.artifact_ref.type != "opportunity")
        ):
            raise DomainError("INVALID_RUN_STATE", "Public maintenance must complete one task", 409)

    async def publish(self, context: StageContext, result: StageResult) -> bool:
        """WorkflowRepository publication: checkpoint first, then a fenced transition."""
        self.validate_result(result)
        async with self.transaction() as session:
            run, job = await self._locked(session, context)
            if job is None:
                return False
            if run and (run.cancel_requested or run.status in TERMINAL):
                self._release(job, JobStatus.CANCELLED)
                if run.status not in TERMINAL:
                    self._state(run, RunStatus.CANCELLED)
                    await self._event(session, run, "CANCELLED")
                return False
            committed = await self._checkpoint(session, job)
            if committed != result:
                raise DomainError("INVALID_RUN_STATE", "Stage must commit before transition", 409)
            if run and run.profile_version_id is not None:
                current = await session.scalar(
                    select(ProfileRecord.current_version_id).where(
                        ProfileRecord.owner_id == run.owner_id
                    )
                )
                if current != run.profile_version_id:
                    self._release(job, JobStatus.FAILED)
                    await self._failed(session, run, "VERSION_CONFLICT")
                    return False
            self._release(job, JobStatus.SUCCEEDED)
            if run:
                self._state(run, result.status)
                run.warnings = list(dict.fromkeys([*run.warnings, *result.warning_codes]))
                if result.artifact_ref:
                    self._append_ref(run, result.artifact_ref)
                if result.next_stage:
                    run.stage = result.next_stage
                    next_id = uuid4()
                    session.add(
                        JobRecord(
                            id=next_id,
                            scope=self.scope,
                            owner_id=run.owner_id,
                            run_id=run.id,
                            stage=result.next_stage,
                            stage_key=logical_key(job.stage_key, result.next_stage),
                            status=JobStatus.QUEUED,
                            due_at=self.clock.now(),
                            deadline_at=run.deadline_at,
                            created_at=self.clock.now(),
                        )
                    )
                    await session.flush()
                    session.add(
                        OutboxRecord(
                            id=uuid4(),
                            scope=self.scope,
                            owner_id=run.owner_id,
                            run_id=run.id,
                            event_key=f"ready:{next_id}",
                            event_type="JOB_READY",
                            payload={"job_id": str(next_id)},
                            status=OutboxStatus.PENDING,
                            created_at=self.clock.now(),
                        )
                    )
                await self._event(session, run, "STAGE_COMPLETED", result.artifact_ref)
            return True

    def _append_ref(self, run: RunRecord, artifact: ArtifactRef) -> None:
        values = run.result_refs.model_dump()
        key = {
            "opportunity": "opportunity_ids",
            "evaluation": "evaluation_ids",
            "draft": "draft_ids",
        }[artifact.type]
        values[key] = tuple(dict.fromkeys([*values[key], artifact.id]))
        run.result_refs = RunResultRefs.model_validate(values)

    async def _failed(self, session: AsyncSession, run: RunRecord, code: str) -> None:
        useful = await session.scalar(
            select(StageOutputRecord.stage_key)
            .where(StageOutputRecord.run_id == run.id, StageOutputRecord.owner_id == run.owner_id)
            .limit(1)
        )
        self._state(run, RunStatus.PARTIAL if useful else RunStatus.FAILED, code)
        await self._event(session, run, code)

    async def fail(self, claim: Claim, code: str, delay: float | None = None) -> bool:
        if re.fullmatch(r"[A-Z][A-Z0-9_]{0,99}", code) is None or (
            delay is not None and (not math.isfinite(delay) or delay < 0)
        ):
            raise ValueError("Failures require a safe code and bounded nonnegative delay")
        async with self.transaction() as session:
            run, job = await self._locked(
                session, claim.context, claim.worker_id, allow_deadline_failure=True
            )
            if job is None:
                return False
            if run and run.cancel_requested:
                self._release(job, JobStatus.CANCELLED)
                self._state(run, RunStatus.CANCELLED)
                await self._event(session, run, "CANCELLED")
            elif (
                delay is not None
                and job.attempt < min(job.max_attempts, 3)
                and (
                    self.clock.now() + timedelta(seconds=delay)
                    < min(job.deadline_at, claim.context.deadline_at)
                )
            ):
                self._release(job, JobStatus.QUEUED)
                job.due_at = self.clock.now() + timedelta(seconds=delay)
                if run:
                    self._state(run, RunStatus.QUEUED)
                    await self._event(session, run, "STAGE_RETRY")
            else:
                self._release(job, JobStatus.FAILED)
                if run:
                    await self._failed(session, run, code)
            return True

    async def cancel(self, actor: ActorContext, run_id: UUID) -> bool:
        if not self._owns(actor):
            raise DomainError("NOT_FOUND", "Run is unavailable", 404)
        async with self.transaction() as session:
            run = await self._run(session, run_id)
            if run is None:
                raise DomainError("NOT_FOUND", "Run is unavailable", 404)
            if run.status in TERMINAL or run.cancel_requested:
                return False
            run.cancel_requested = True
            run.revision += 1
            run.updated_at = self.clock.now()
            await self._event(session, run, "CANCEL_REQUESTED")
            return True

    async def get_run(self, actor: ActorContext, run_id: UUID) -> Run | None:
        if not self._owns(actor):
            return None
        async with self.transaction() as session:
            run = await self._run(session, run_id)
            if run is None:
                return None
            return Run(
                id=run.id,
                kind=run.kind,
                status=run.status,
                stage=run.stage,
                profile_version_id=run.profile_version_id,
                cancel_requested=run.cancel_requested,
                progress=run.progress,
                funnel=run.funnel,
                result_refs=run.result_refs,
                warnings=tuple(run.warnings),
                failure_code=run.failure_code,
                created_at=run.created_at.astimezone(UTC),
                updated_at=run.updated_at.astimezone(UTC),
            )

    async def events(
        self, actor: ActorContext, run_id: UUID, *, after_seq: int, limit: int
    ) -> tuple[RunEvent, ...]:
        if not self._owns(actor) or not 1 <= limit <= 100 or after_seq < -1:
            raise DomainError("NOT_FOUND", "Run is unavailable", 404)
        async with self.transaction() as session:
            if await self._run(session, run_id) is None:
                raise DomainError("NOT_FOUND", "Run is unavailable", 404)
            cutoff = self.clock.now() - timedelta(hours=24)
            if after_seq >= 0:
                cursor_at = await session.scalar(
                    select(RunEventRecord.at).where(
                        RunEventRecord.owner_id == actor.owner_id,
                        RunEventRecord.run_id == run_id,
                        RunEventRecord.seq == after_seq,
                    )
                )
                if cursor_at is None or cursor_at < cutoff:
                    raise DomainError("EVENT_CURSOR_EXPIRED", "Read the current run status", 410)
            return tuple(
                await session.scalars(
                    select(RunEventRecord.payload)
                    .where(
                        RunEventRecord.owner_id == actor.owner_id,
                        RunEventRecord.run_id == run_id,
                        RunEventRecord.seq > after_seq,
                        RunEventRecord.at >= cutoff,
                    )
                    .order_by(RunEventRecord.seq)
                    .limit(limit)
                )
            )
