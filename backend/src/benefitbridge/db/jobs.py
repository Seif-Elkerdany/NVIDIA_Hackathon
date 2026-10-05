"""MS-015 durable work schema, independent of dispatch/provider execution.

Use verified ActorContext and the existing owner_transaction for private writes.
Commit runs, initial jobs, outbox, events and encrypted replay in one transaction.
Public work uses separate credentials; never grant its role to a private worker.
MS-016 owns claims/publication; MS-019 owns global -> owner -> run budget locks.
"""

import json
import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    LargeBinary,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from benefitbridge.db.base import Base
from benefitbridge.db.sources import ModelJson
from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.dto import ArtifactRef, RunEvent, RunFunnel, RunProgress, RunResultRefs
from benefitbridge.domain.enums import DeletionStatus, RunKind, RunStatus
from benefitbridge.ports import JobScope

REPLAY_PREFIX = b"BBREPLAY1"
MAX_REPLAY_BYTES = 256 * 1024
SCOPE_CHECK = (
    "(scope = 'PRIVATE' AND owner_id IS NOT NULL AND run_id IS NOT NULL) OR "
    "(scope = 'PUBLIC' AND owner_id IS NULL AND run_id IS NULL)"
)


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OutboxStatus(StrEnum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"


class ReservationStatus(StrEnum):
    RESERVED = "RESERVED"
    BILLING_UNKNOWN = "BILLING_UNKNOWN"
    RECONCILED = "RECONCILED"
    RELEASED = "RELEASED"


class UsageStatus(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


class RunRecord(Base):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_runs_owner_id_id"),
        ForeignKeyConstraint(
            ["owner_id", "profile_version_id"], ["profile_versions.owner_id", "profile_versions.id"]
        ),
        CheckConstraint("deletion_epoch >= 0 AND revision > 0", name="version"),
        CheckConstraint("jsonb_typeof(inputs) = 'object'", name="inputs_object"),
        CheckConstraint(
            "jsonb_typeof(progress) = 'object' AND jsonb_typeof(funnel) = 'object' "
            "AND jsonb_typeof(result_refs) = 'object' AND jsonb_typeof(warnings) = 'array'",
            name="result_shapes",
        ),
        CheckConstraint("char_length(stage) BETWEEN 1 AND 100", name="stage"),
        CheckConstraint("deadline_at > created_at AND updated_at >= created_at", name="times"),
        Index("ix_runs_owner_created", "owner_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    kind: Mapped[RunKind] = mapped_column(Enum(RunKind, native_enum=False, create_constraint=True))
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, native_enum=False, create_constraint=True)
    )
    inputs: Mapped[dict[str, object]] = mapped_column(JSONB)
    progress: Mapped[RunProgress] = mapped_column(
        ModelJson(RunProgress),
        server_default=text("jsonb_build_object('completed_units', 0, 'total_units', NULL)"),
    )
    funnel: Mapped[RunFunnel] = mapped_column(
        ModelJson(RunFunnel),
        server_default=text(
            "jsonb_build_object('raw_hits', 0, 'canonical', 0, 'official', 0, "
            "'parsed', 0, 'evaluated', 0)"
        ),
    )
    result_refs: Mapped[RunResultRefs] = mapped_column(
        ModelJson(RunResultRefs),
        server_default=text(
            "jsonb_build_object('opportunity_ids', jsonb_build_array(), "
            "'evaluation_ids', jsonb_build_array(), 'draft_ids', jsonb_build_array())"
        ),
    )
    warnings: Mapped[list[str]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    failure_code: Mapped[str | None] = mapped_column(String(100))
    profile_version_id: Mapped[UUID | None] = mapped_column()
    deletion_epoch: Mapped[int] = mapped_column()
    stage: Mapped[str] = mapped_column(String(100))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JobRecord(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_jobs_owner_id_id"),
        UniqueConstraint("owner_id", "run_id", "stage_key", "id", name="uq_jobs_stage_identity"),
        UniqueConstraint("run_id", "stage_key", name="uq_jobs_run_stage"),
        ForeignKeyConstraint(
            ["owner_id", "run_id"], ["runs.owner_id", "runs.id"], ondelete="CASCADE"
        ),
        CheckConstraint(SCOPE_CHECK, name="scope"),
        CheckConstraint(
            "char_length(stage_key) BETWEEN 1 AND 256 AND char_length(stage) BETWEEN 1 AND 100",
            name="stage",
        ),
        CheckConstraint(
            "attempt >= 0 AND max_attempts > 0 AND attempt <= max_attempts "
            "AND fencing_token >= 0 AND revision > 0",
            name="counters",
        ),
        CheckConstraint("deadline_at > created_at AND due_at <= deadline_at", name="deadline"),
        CheckConstraint(
            "(status = 'RUNNING' AND lease_owner IS NOT NULL AND lease_until IS NOT NULL "
            "AND fencing_token > 0 AND lease_until <= deadline_at) OR "
            "(status <> 'RUNNING' AND lease_owner IS NULL AND lease_until IS NULL)",
            name="lease",
        ),
        CheckConstraint(
            "scope <> 'PUBLIC' OR source_id IS NOT NULL OR opportunity_id IS NOT NULL "
            "OR snapshot_id IS NOT NULL",
            name="public_target",
        ),
        Index(
            "ix_jobs_public_stage",
            "stage_key",
            unique=True,
            postgresql_where=text("scope = 'PUBLIC'"),
        ),
        Index("ix_jobs_due", "scope", "due_at", postgresql_where=text("status = 'QUEUED'")),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    scope: Mapped[JobScope] = mapped_column(Enum(JobScope, native_enum=False))
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    run_id: Mapped[UUID | None] = mapped_column()
    source_id: Mapped[UUID | None] = mapped_column(ForeignKey("sources.id"))
    opportunity_id: Mapped[UUID | None] = mapped_column(ForeignKey("opportunities.id"))
    snapshot_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_snapshots.id"))
    stage: Mapped[str] = mapped_column(String(100))
    stage_key: Mapped[str] = mapped_column(String(256))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, create_constraint=True)
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempt: Mapped[int] = mapped_column(server_default=text("0"))
    max_attempts: Mapped[int] = mapped_column(server_default=text("3"))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_owner: Mapped[UUID | None] = mapped_column()
    fencing_token: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OutboxRecord(Base):
    __tablename__ = "outbox"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_outbox_owner_id_id"),
        UniqueConstraint("run_id", "event_key", name="uq_outbox_run_event"),
        ForeignKeyConstraint(
            ["owner_id", "run_id"], ["runs.owner_id", "runs.id"], ondelete="CASCADE"
        ),
        CheckConstraint(SCOPE_CHECK, name="scope"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
        CheckConstraint(
            "char_length(event_key) BETWEEN 1 AND 256 AND "
            "char_length(event_type) BETWEEN 1 AND 100",
            name="event",
        ),
        CheckConstraint("revision > 0", name="revision"),
        Index(
            "ix_outbox_public_event",
            "event_key",
            unique=True,
            postgresql_where=text("scope = 'PUBLIC'"),
        ),
        Index(
            "ix_outbox_pending", "scope", "created_at", postgresql_where=text("status = 'PENDING'")
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    scope: Mapped[JobScope] = mapped_column(Enum(JobScope, native_enum=False))
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    run_id: Mapped[UUID | None] = mapped_column()
    event_key: Mapped[str] = mapped_column(String(256))
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict[str, object]] = mapped_column(JSONB)
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus, native_enum=False, create_constraint=True)
    )
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RunEventRecord(Base):
    __tablename__ = "run_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_id", "run_id"], ["runs.owner_id", "runs.id"], ondelete="CASCADE"
        ),
        CheckConstraint("seq >= 0", name="seq"),
        CheckConstraint("char_length(event_type) BETWEEN 1 AND 100", name="event_type"),
    )
    owner_id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[RunEvent] = mapped_column(ModelJson(RunEvent))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StageOutputRecord(Base):
    __tablename__ = "stage_outputs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_id", "run_id"], ["runs.owner_id", "runs.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["owner_id", "run_id", "stage_key", "job_id"],
            ["jobs.owner_id", "jobs.run_id", "jobs.stage_key", "jobs.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("fencing_token > 0", name="fencing_token"),
    )
    owner_id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID] = mapped_column(primary_key=True)
    stage_key: Mapped[str] = mapped_column(String(256), primary_key=True)
    job_id: Mapped[UUID] = mapped_column()
    fencing_token: Mapped[int] = mapped_column(BigInteger)
    artifact_ref: Mapped[ArtifactRef] = mapped_column(ModelJson(ArtifactRef))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        CheckConstraint(
            "char_length(operation) BETWEEN 1 AND 100 AND char_length(key) BETWEEN 16 AND 128",
            name="identity",
        ),
        CheckConstraint("request_hash ~ '^[0-9a-f]{64}$'", name="request_hash"),
        CheckConstraint(
            "octet_length(response_ciphertext) BETWEEN 38 AND 262181 AND "
            "substring(response_ciphertext FROM 1 FOR 9) = "
            "decode('42425245504c415931', 'hex')",
            name="encrypted_replay",
        ),
        CheckConstraint("response_status BETWEEN 200 AND 599", name="response_status"),
        CheckConstraint("expires_at = created_at + interval '24 hours'", name="retention"),
        Index("ix_idempotency_records_expires", "expires_at"),
    )
    # The DELETE replay exception outlives account purge for its 24h TTL.
    # Migration triggers verify the owner at insertion and purge ordinary replays.
    owner_id: Mapped[UUID] = mapped_column(primary_key=True)
    operation: Mapped[str] = mapped_column(String(100), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response_ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    response_status: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UsageReservationRecord(Base):
    __tablename__ = "usage_reservations"
    __table_args__ = (
        UniqueConstraint("scope", "id", name="uq_usage_reservations_scope_id"),
        UniqueConstraint(
            "id", "registry_version", "price_version", name="uq_usage_reservations_price_context"
        ),
        UniqueConstraint("owner_id", "run_id", "id", name="uq_usage_reservations_private_id"),
        ForeignKeyConstraint(
            ["owner_id", "run_id"], ["runs.owner_id", "runs.id"], ondelete="CASCADE"
        ),
        CheckConstraint(SCOPE_CHECK, name="scope"),
        CheckConstraint("amount >= 0 AND revision > 0", name="amount_revision"),
        CheckConstraint(
            "expires_at > created_at AND char_length(registry_version) > 0 AND "
            "char_length(price_version) > 0",
            name="provenance",
        ),
        Index("ix_usage_reservations_scope_created", "scope", "created_at"),
        Index("ix_usage_reservations_owner_created", "owner_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    scope: Mapped[JobScope] = mapped_column(Enum(JobScope, native_enum=False))
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    run_id: Mapped[UUID | None] = mapped_column()
    amount: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, native_enum=False, create_constraint=True)
    )
    registry_version: Mapped[str] = mapped_column(String(100))
    price_version: Mapped[str] = mapped_column(String(100))
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UsageEntryRecord(Base):
    __tablename__ = "usage_entries"
    __table_args__ = (
        UniqueConstraint("reservation_id", name="uq_usage_entries_reservation"),
        ForeignKeyConstraint(
            ["reservation_id", "registry_version", "price_version"],
            [
                "usage_reservations.id",
                "usage_reservations.registry_version",
                "usage_reservations.price_version",
            ],
            name="fk_usage_entries_price_context",
        ),
        ForeignKeyConstraint(
            ["scope", "reservation_id"], ["usage_reservations.scope", "usage_reservations.id"]
        ),
        ForeignKeyConstraint(
            ["owner_id", "run_id", "reservation_id"],
            ["usage_reservations.owner_id", "usage_reservations.run_id", "usage_reservations.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(SCOPE_CHECK, name="scope"),
        CheckConstraint(
            "(status = 'KNOWN' AND cost IS NOT NULL AND cost >= 0) OR "
            "(status = 'UNKNOWN' AND cost IS NULL)",
            name="billing",
        ),
        CheckConstraint(
            "jsonb_typeof(provider_usage) = 'object' AND "
            "provider_usage - ARRAY['input_tokens','output_tokens','provider_request_id'] "
            "= '{}'::jsonb",
            name="usage_payload",
        ),
        CheckConstraint(
            "(NOT provider_usage ? 'input_tokens' OR "
            "(jsonb_typeof(provider_usage->'input_tokens') = 'number' AND "
            "(provider_usage->>'input_tokens')::numeric >= 0 AND "
            "trunc((provider_usage->>'input_tokens')::numeric) = "
            "(provider_usage->>'input_tokens')::numeric)) AND "
            "(NOT provider_usage ? 'output_tokens' OR "
            "(jsonb_typeof(provider_usage->'output_tokens') = 'number' AND "
            "(provider_usage->>'output_tokens')::numeric >= 0 AND "
            "trunc((provider_usage->>'output_tokens')::numeric) = "
            "(provider_usage->>'output_tokens')::numeric)) AND "
            "(NOT provider_usage ? 'provider_request_id' OR "
            "(jsonb_typeof(provider_usage->'provider_request_id') = 'string' AND "
            "provider_usage->>'provider_request_id' ~ '^[A-Za-z0-9_.:-]{1,128}$'))",
            name="usage_values",
        ),
        CheckConstraint(
            "char_length(registry_version) > 0 AND char_length(price_version) > 0",
            name="provenance",
        ),
        CheckConstraint("revision > 0", name="revision"),
        Index("ix_usage_entries_scope_created", "scope", "created_at"),
        Index("ix_usage_entries_owner_created", "owner_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    scope: Mapped[JobScope] = mapped_column(Enum(JobScope, native_enum=False))
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    run_id: Mapped[UUID | None] = mapped_column()
    reservation_id: Mapped[UUID] = mapped_column()
    provider_usage: Mapped[dict[str, object]] = mapped_column(JSONB)
    cost: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[UsageStatus] = mapped_column(Enum(UsageStatus, native_enum=False))
    registry_version: Mapped[str] = mapped_column(String(100))
    price_version: Mapped[str] = mapped_column(String(100))
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DeletionReceiptRecord(Base):
    __tablename__ = "deletion_receipts"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_deletion_receipts_token_hash"),
        CheckConstraint("octet_length(token_hash) = 32", name="token_hash"),
        CheckConstraint(
            "expires_at = requested_at + interval '168 hours' AND revision > 0",
            name="retention_revision",
        ),
        CheckConstraint(
            "status <> 'COMPLETE' OR active_store_deleted_at IS NOT NULL", name="completion"
        ),
        Index("ix_deletion_receipts_expires", "expires_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    token_hash: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[DeletionStatus] = mapped_column(
        Enum(DeletionStatus, native_enum=False, create_constraint=True)
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    active_store_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    backup_retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(server_default=text("1"))


@dataclass(frozen=True)
class ReplayIdentity:
    owner_id: UUID
    operation: str
    key: str
    request_hash: str

    def aad(self) -> bytes:
        return json.dumps(
            [str(self.owner_id), self.operation, self.key, self.request_hash], separators=(",", ":")
        ).encode("utf-8")


def encrypt_replay(body: DomainModel, identity: ReplayIdentity, *, encryption_key: bytes) -> bytes:
    """AES-256-GCM binds a replay to its owner, operation, key and request hash."""
    if len(encryption_key) != 32:
        raise ValueError("Replay encryption requires a 32-byte AES key")
    payload = body.model_dump_json().encode("utf-8")
    if len(payload) > MAX_REPLAY_BYTES:
        raise ValueError("Replay exceeds the API body limit")
    nonce = secrets.token_bytes(12)
    return REPLAY_PREFIX + nonce + AESGCM(encryption_key).encrypt(nonce, payload, identity.aad())


def decrypt_replay(ciphertext: bytes, identity: ReplayIdentity, *, encryption_key: bytes) -> bytes:
    """Authenticated bytes only; the caller checks expiry and decodes its original DTO."""
    if len(encryption_key) != 32 or not ciphertext.startswith(REPLAY_PREFIX):
        raise ValueError("Invalid encrypted replay")
    if not 38 <= len(ciphertext) <= MAX_REPLAY_BYTES + 37:
        raise ValueError("Invalid encrypted replay size")
    return AESGCM(encryption_key).decrypt(ciphertext[9:21], ciphertext[21:], identity.aad())
