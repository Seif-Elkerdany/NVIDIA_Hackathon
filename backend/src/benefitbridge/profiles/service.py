"""Immutable owner profile publication with encrypted replay and durable invalidation."""

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import UTC, timedelta
from hashlib import sha256
from hmac import compare_digest, digest
from uuid import UUID, uuid4

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from benefitbridge.db.base import owner_transaction
from benefitbridge.db.documents import EvidenceSpanRecord, FactCandidateRecord, FactEvidenceRecord
from benefitbridge.db.jobs import (
    IdempotencyRecord,
    JobRecord,
    JobStatus,
    OutboxRecord,
    OutboxStatus,
    ReplayIdentity,
    RunRecord,
    decrypt_replay,
    encrypt_replay,
)
from benefitbridge.db.profiles import (
    AccountRecord,
    FactRecord,
    ProfileRecord,
    ProfileVersionFactRecord,
    ProfileVersionRecord,
)
from benefitbridge.domain.dto import Envelope, Page, Profile
from benefitbridge.domain.enums import Provenance, RunKind, RunStatus
from benefitbridge.domain.errors import DomainError
from benefitbridge.domain.facts import Fact, FactInput
from benefitbridge.domain.requests import PatchProfile
from benefitbridge.ports import ActorContext, Clock, JobScope


@dataclass(frozen=True)
class Publication:
    body: Envelope[Profile]
    replayed: bool


class ProfileService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        clock: Clock,
        *,
        key: bytes,
        notice_version: str,
    ) -> None:
        if len(key) < 32:
            raise ValueError("Profile replay/cursor secret requires at least 32 bytes")
        self.sessions, self.clock = sessions, clock
        self.key = sha256(b"benefitbridge:profile:v1:" + key).digest()
        self.notice_version = notice_version

    async def _profile(self, session: AsyncSession, actor: ActorContext) -> ProfileRecord:
        row = (
            await session.execute(
                select(ProfileRecord)
                .where(ProfileRecord.owner_id == actor.owner_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise DomainError("NOT_FOUND", "Profile is unavailable.", 404)
        return row

    async def _view(
        self,
        session: AsyncSession,
        actor: ActorContext,
        profile: ProfileRecord,
        version: ProfileVersionRecord,
    ) -> Profile:
        rows = (
            await session.scalars(
                select(FactRecord)
                .join(
                    ProfileVersionFactRecord,
                    (ProfileVersionFactRecord.fact_id == FactRecord.id)
                    & (ProfileVersionFactRecord.owner_id == FactRecord.owner_id),
                )
                .where(
                    ProfileVersionFactRecord.owner_id == actor.owner_id,
                    ProfileVersionFactRecord.version_id == version.id,
                )
                .order_by(FactRecord.attribute)
            )
        ).all()
        facts: list[Fact] = []
        for row in rows:
            links = (
                await session.scalars(
                    select(FactEvidenceRecord)
                    .where(
                        FactEvidenceRecord.owner_id == actor.owner_id,
                        FactEvidenceRecord.fact_id == row.id,
                    )
                    .order_by(FactEvidenceRecord.evidence_id)
                )
            ).all()
            # RLS removes support from tombstoned documents even in history.
            if row.provenance == Provenance.USER_CONFIRMED_DOCUMENT and not links:
                continue
            facts.append(
                Fact(
                    id=row.id,
                    attribute=row.attribute,
                    value=row.typed_value,
                    evidence_ids=tuple(link.evidence_id for link in links),
                    provenance=row.provenance,
                    confirmed_at=row.confirmed_at.astimezone(UTC),
                    valid_from=row.valid_from,
                    valid_until=row.valid_until,
                    conflict=row.conflict,
                )
            )
        return Profile(
            id=profile.id,
            version_id=version.id,
            version_number=version.version_number,
            facts=tuple(facts),
            updated_at=version.created_at.astimezone(UTC),
        )

    async def get(self, actor: ActorContext, version_id: UUID | None = None) -> Profile:
        async with owner_transaction(self.sessions, actor) as session:
            profile = await self._profile(session, actor)
            version = await session.scalar(
                select(ProfileVersionRecord).where(
                    ProfileVersionRecord.owner_id == actor.owner_id,
                    ProfileVersionRecord.id == (version_id or profile.current_version_id),
                )
            )
            if version is None:
                raise DomainError("NOT_FOUND", "Profile version is unavailable.", 404)
            return await self._view(session, actor, profile, version)

    def _cursor(self, actor: ActorContext, version: ProfileVersionRecord) -> str:
        data = json.dumps(
            [str(actor.owner_id), version.version_number, str(version.id)],
            separators=(",", ":"),
        ).encode()
        return (
            base64.urlsafe_b64encode(data + digest(self.key, b"profile-versions:" + data, "sha256"))
            .decode()
            .rstrip("=")
        )

    def _decode_cursor(self, actor: ActorContext, cursor: str) -> tuple[int, UUID]:
        try:
            if len(cursor) > 1024:
                raise ValueError
            raw = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
            data, signature = raw[:-32], raw[-32:]
            if not compare_digest(
                signature, digest(self.key, b"profile-versions:" + data, "sha256")
            ):
                raise ValueError
            owner, ordinal, version = json.loads(data)
            if owner != str(actor.owner_id) or type(ordinal) is not int or ordinal < 1:
                raise ValueError
            return ordinal, UUID(version)
        except (ValueError, TypeError, binascii.Error, UnicodeDecodeError):
            raise DomainError("INVALID_CURSOR", "Profile history cursor is invalid.", 400) from None

    async def list(self, actor: ActorContext, *, limit: int, cursor: str | None) -> Page[Profile]:
        if not 1 <= limit <= 100:
            raise DomainError("BAD_REQUEST", "History limit must be 1 to 100.", 400)
        position = self._decode_cursor(actor, cursor) if cursor is not None else None
        async with owner_transaction(self.sessions, actor) as session:
            profile = await self._profile(session, actor)
            query = select(ProfileVersionRecord).where(
                ProfileVersionRecord.owner_id == actor.owner_id
            )
            if position:
                query = query.where(
                    tuple_(ProfileVersionRecord.version_number, ProfileVersionRecord.id) < position
                )
            versions = (
                await session.scalars(
                    query.order_by(
                        ProfileVersionRecord.version_number.desc(), ProfileVersionRecord.id.desc()
                    ).limit(limit + 1)
                )
            ).all()
            selected = versions[:limit]
            return Page(
                items=tuple([await self._view(session, actor, profile, row) for row in selected]),
                next_cursor=self._cursor(actor, selected[-1]) if len(versions) > limit else None,
            )

    async def _support(self, session: AsyncSession, actor: ActorContext, change: FactInput) -> None:
        for evidence_id in change.evidence_ids:
            span = await session.scalar(
                select(EvidenceSpanRecord).where(
                    EvidenceSpanRecord.owner_id == actor.owner_id,
                    EvidenceSpanRecord.id == evidence_id,
                )
            )
            candidates = (
                await session.scalars(
                    select(FactCandidateRecord).where(
                        FactCandidateRecord.owner_id == actor.owner_id,
                        FactCandidateRecord.document_id == (span.document_id if span else None),
                    )
                )
            ).all()
            if span is None or not any(
                candidate.candidate.state.value != "REJECTED"
                and candidate.candidate.attribute == change.attribute
                and candidate.candidate.value == change.value
                and evidence_id in candidate.candidate.evidence_ids
                for candidate in candidates
            ):
                raise DomainError("EVIDENCE_UNAVAILABLE", "Matching evidence is unavailable.", 404)

    async def patch(self, actor: ActorContext, payload: PatchProfile, key: str) -> Publication:
        canonical = json.dumps(
            payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        request_hash = sha256(canonical.encode()).hexdigest()
        identity = ReplayIdentity(actor.owner_id, "patch_profile", key, request_hash)
        now = self.clock.now()
        async with owner_transaction(self.sessions, actor) as session:
            profile = await self._profile(session, actor)
            replay = await session.get(IdempotencyRecord, (actor.owner_id, "patch_profile", key))
            consent = await session.scalar(
                select(AccountRecord.consent_version).where(AccountRecord.id == actor.owner_id)
            )
            if consent != self.notice_version:
                raise DomainError(
                    "CONSENT_REQUIRED", "Current processing consent is required.", 403
                )
            if replay is not None:
                if replay.expires_at <= now:
                    # Expired immutable replay keys are cleaned by maintenance;
                    # never overwrite them or replay stale private content.
                    raise DomainError("IDEMPOTENCY_CONFLICT", "Use a new idempotency key.", 409)
                if replay.request_hash != request_hash:
                    raise DomainError(
                        "IDEMPOTENCY_CONFLICT", "Key already used for a different patch.", 409
                    )
                body = Envelope[Profile].model_validate_json(
                    decrypt_replay(replay.response_ciphertext, identity, encryption_key=self.key)
                )
                for fact in body.data.facts:
                    for evidence_id in fact.evidence_ids:
                        visible = await session.scalar(
                            select(EvidenceSpanRecord.id).where(
                                EvidenceSpanRecord.owner_id == actor.owner_id,
                                EvidenceSpanRecord.id == evidence_id,
                            )
                        )
                        if visible is None:
                            raise DomainError(
                                "EVIDENCE_UNAVAILABLE", "Replay evidence is unavailable.", 404
                            )
                return Publication(body, True)
            if profile.current_version_id != payload.base_profile_version_id:
                raise DomainError(
                    "VERSION_CONFLICT", "Reload the current profile before editing.", 409
                )
            current = (
                await session.execute(
                    select(ProfileVersionRecord).where(
                        ProfileVersionRecord.owner_id == actor.owner_id,
                        ProfileVersionRecord.id == profile.current_version_id,
                    )
                )
            ).scalar_one()
            members = (
                await session.scalars(
                    select(ProfileVersionFactRecord).where(
                        ProfileVersionFactRecord.owner_id == actor.owner_id,
                        ProfileVersionFactRecord.version_id == current.id,
                    )
                )
            ).all()
            retained = {
                row.attribute: row.fact_id
                for row in members
                if row.attribute not in payload.remove_attributes
            }
            for change in payload.changes:
                await self._support(session, actor, change)
                fact_id = uuid4()
                session.add(
                    FactRecord(
                        id=fact_id,
                        owner_id=actor.owner_id,
                        attribute=change.attribute,
                        typed_value=change.value,
                        provenance=Provenance.USER_CONFIRMED_DOCUMENT
                        if change.evidence_ids
                        else Provenance.USER_CONFIRMED,
                        confirmed_at=now,
                        conflict=False,
                    )
                )
                await session.flush()
                for evidence_id in change.evidence_ids:
                    session.add(
                        FactEvidenceRecord(
                            owner_id=actor.owner_id,
                            fact_id=fact_id,
                            evidence_id=evidence_id,
                            supported_value=change.value,
                            independently_confirmed=True,
                        )
                    )
                retained[change.attribute] = fact_id
            version = ProfileVersionRecord(
                id=uuid4(),
                owner_id=actor.owner_id,
                version_number=current.version_number + 1,
                created_at=now,
            )
            session.add(version)
            await session.flush()
            for attribute, fact_id in retained.items():
                session.add(
                    ProfileVersionFactRecord(
                        owner_id=actor.owner_id,
                        version_id=version.id,
                        attribute=attribute,
                        fact_id=fact_id,
                    )
                )
            profile.current_version_id = version.id
            # MS-015 private outbox entries require a durable owner-bound run.
            # This pending evaluation-maintenance stage records invalidation, not
            # a fabricated successful evaluation. MS-062 consumes PROFILE_CHANGED.
            run_id = uuid4()
            session.add(
                RunRecord(
                    id=run_id,
                    owner_id=actor.owner_id,
                    kind=RunKind.EVALUATE,
                    status=RunStatus.QUEUED,
                    inputs={"profile_version_id": str(version.id)},
                    profile_version_id=version.id,
                    deletion_epoch=actor.deletion_epoch,
                    stage="PROFILE_INVALIDATE",
                    deadline_at=now + timedelta(seconds=180),
                    created_at=now,
                    updated_at=now,
                )
            )
            await session.flush()
            session.add(
                JobRecord(
                    id=uuid4(),
                    scope=JobScope.PRIVATE,
                    owner_id=actor.owner_id,
                    run_id=run_id,
                    stage="PROFILE_INVALIDATE",
                    stage_key=f"profile:{version.id}",
                    status=JobStatus.QUEUED,
                    due_at=now,
                    deadline_at=now + timedelta(seconds=180),
                    created_at=now,
                )
            )
            session.add(
                OutboxRecord(
                    id=uuid4(),
                    scope=JobScope.PRIVATE,
                    owner_id=actor.owner_id,
                    run_id=run_id,
                    event_key=f"profile:{version.id}",
                    event_type="PROFILE_CHANGED",
                    payload={
                        "profile_version_id": str(version.id),
                        "previous_version_id": str(current.id),
                    },
                    status=OutboxStatus.PENDING,
                    created_at=now,
                )
            )
            await session.flush()
            body = Envelope(
                data=await self._view(session, actor, profile, version), request_id=actor.request_id
            )
            session.add(
                IdempotencyRecord(
                    owner_id=actor.owner_id,
                    operation="patch_profile",
                    key=key,
                    request_hash=request_hash,
                    response_ciphertext=encrypt_replay(body, identity, encryption_key=self.key),
                    response_status=200,
                    created_at=now,
                    expires_at=now + timedelta(hours=24),
                )
            )
            return Publication(body, False)
