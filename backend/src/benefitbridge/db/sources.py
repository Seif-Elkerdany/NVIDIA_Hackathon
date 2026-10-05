"""MS-014 public catalog tables; public rows must never contain applicant data.

Writers use short explicit transactions and server-generated UUIDs. Snapshot
reuse is scoped to source + normalized hash; each check still creates a fetch
audit row with its own raw hash. Authority resolution belongs to MS-032.
"""

from datetime import datetime
from uuid import UUID

from pydantic import StrictBool
from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from benefitbridge.db.base import Base
from benefitbridge.domain.base import DomainModel, HttpsUrl, NonEmpty, PositiveInt
from benefitbridge.domain.dto import Deadline, SourceSpan
from benefitbridge.domain.enums import Authority, Availability, Completeness, Lane
from benefitbridge.sources.contracts import NormalizedText, SourceSnapshot


class ModelJson[T: DomainModel](TypeDecorator[T]):
    """Reuse domain validation on both bind and load, including normalized spans."""

    impl = JSONB
    cache_ok = True

    def __init__(self, model: type[T]) -> None:
        super().__init__()
        self.model = model

    def process_bind_param(self, value: T | None, dialect: Dialect) -> object:
        if value is None:
            return None
        return self.model.model_validate(value).model_dump(mode="json")

    def process_result_value(self, value: object, dialect: Dialect) -> T:
        return self.model.model_validate(value)


class ProviderPolicy(DomainModel):
    """Registry evidence is explicit; a hostname alone is not officiality proof."""

    version: PositiveInt
    affiliation_evidence: tuple[HttpsUrl, ...]
    notes: NonEmpty


class OpportunityMetadata(DomainModel):
    """Public version input only: no user evaluation/freshness response fields."""

    title: NonEmpty
    lane: Lane
    remote: StrictBool
    official_url: HttpsUrl
    authority: Authority
    availability: Availability
    deadline: Deadline


class ProviderRecord(Base):
    __tablename__ = "providers"
    __table_args__ = (
        CheckConstraint("char_length(name) > 0", name="name"),
        CheckConstraint(
            "cardinality(domains) > 0 AND array_position(domains, NULL) IS NULL", name="domains"
        ),
        CheckConstraint("jsonb_typeof(policies) = 'object'", name="policies_object"),
        CheckConstraint("revision > 0", name="revision"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    domains: Mapped[list[str]] = mapped_column(ARRAY(Text))
    policies: Mapped[ProviderPolicy] = mapped_column(ModelJson(ProviderPolicy))
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceRecord(Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("canonical_url", name="uq_sources_canonical_url"),
        CheckConstraint("canonical_url ~ '^https://[^[:space:]]+$'", name="https_url"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    canonical_url: Mapped[str] = mapped_column(Text)
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("providers.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceSnapshotRecord(Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (
        UniqueConstraint("source_id", "normalized_hash", name="uq_source_snapshots_source_hash"),
        UniqueConstraint("source_id", "id", name="uq_source_snapshots_source_id_id"),
        CheckConstraint("raw_hash ~ '^[0-9a-f]{64}$'", name="raw_hash"),
        CheckConstraint("normalized_hash ~ '^[0-9a-f]{64}$'", name="normalized_hash"),
        CheckConstraint("char_length(text_object_key) > 0", name="object_key"),
        CheckConstraint("jsonb_typeof(normalized) = 'object'", name="normalized_object"),
        CheckConstraint(
            "authority IN ('OFFICIAL','CORROBORATED','DISCOVERY_ONLY','UNRESOLVED')",
            name="authority",
        ),
        CheckConstraint(
            "completeness IN ('COMPLETE','INCOMPLETE','CONFLICTED')", name="completeness"
        ),
        Index("ix_source_snapshots_normalized_hash", "normalized_hash"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"))
    raw_hash: Mapped[str] = mapped_column(String(64))
    normalized_hash: Mapped[str] = mapped_column(String(64))
    text_object_key: Mapped[str] = mapped_column(Text)
    # Retain the MS-006 coordinate space so direct SQL cannot invent a quote.
    normalized: Mapped[NormalizedText] = mapped_column(ModelJson(NormalizedText))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    authority: Mapped[Authority] = mapped_column(Enum(Authority, native_enum=False, length=32))
    completeness: Mapped[Completeness] = mapped_column(
        Enum(Completeness, native_enum=False, length=16)
    )


class SourceSpanRecord(Base):
    __tablename__ = "source_spans"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "id", name="uq_source_spans_snapshot_id_id"),
        CheckConstraint("page IS NULL OR page > 0", name="page"),
        CheckConstraint(
            '"start" >= 0 AND "end" > "start" AND char_length(quote) = "end" - "start"',
            name="offsets",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    snapshot_id: Mapped[UUID] = mapped_column(ForeignKey("source_snapshots.id"), index=True)
    page: Mapped[int | None] = mapped_column()
    start: Mapped[int] = mapped_column()
    end: Mapped[int] = mapped_column()
    quote: Mapped[str] = mapped_column(Text)


class SourceFetchRecord(Base):
    __tablename__ = "source_fetches"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "snapshot_id"], ["source_snapshots.source_id", "source_snapshots.id"]
        ),
        CheckConstraint(
            "http_status IS NULL OR http_status BETWEEN 100 AND 599", name="http_status"
        ),
        CheckConstraint("raw_hash IS NULL OR raw_hash ~ '^[0-9a-f]{64}$'", name="raw_hash"),
        CheckConstraint("snapshot_id IS NULL OR raw_hash IS NOT NULL", name="snapshot_hash"),
        Index("ix_source_fetches_source_checked", "source_id", "checked_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"))
    snapshot_id: Mapped[UUID | None] = mapped_column()
    raw_hash: Mapped[str | None] = mapped_column(String(64))
    http_status: Mapped[int | None] = mapped_column()
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


CANONICAL_KEY_SQL = (
    "provider_id::text || ':' || char_length(external_id)::text || ':' || external_id "
    "|| ':' || char_length(intake)::text || ':' || intake "
    "|| ':' || char_length(location_scope)::text || ':' || location_scope"
)


class OpportunityRecord(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("canonical_key", name="uq_opportunities_canonical_key"),
        UniqueConstraint(
            "provider_id",
            "external_id",
            "intake",
            "location_scope",
            name="uq_opportunities_identity",
        ),
        UniqueConstraint("id", "intake", "location_scope", name="uq_opportunities_scope"),
        CheckConstraint(
            "char_length(external_id) > 0 AND char_length(intake) > 0 AND "
            "char_length(location_scope) > 0",
            name="identity",
        ),
        CheckConstraint("revision > 0", name="revision"),
        ForeignKeyConstraint(
            ["id", "current_version_id"],
            ["opportunity_versions.opportunity_id", "opportunity_versions.id"],
            name="fk_opportunities_current_version",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        Index("ix_opportunities_provider_intake", "provider_id", "intake"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("providers.id"))
    external_id: Mapped[str] = mapped_column(Text)
    intake: Mapped[str] = mapped_column(Text)
    location_scope: Mapped[str] = mapped_column(Text)
    canonical_key: Mapped[str] = mapped_column(Text, Computed(CANONICAL_KEY_SQL, persisted=True))
    current_version_id: Mapped[UUID] = mapped_column()
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OpportunityVersionRecord(Base):
    __tablename__ = "opportunity_versions"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "id", name="uq_opportunity_versions_opportunity_id_id"),
        UniqueConstraint("opportunity_id", "version_number", name="uq_opportunity_versions_number"),
        ForeignKeyConstraint(
            ["opportunity_id", "cycle", "location"],
            ["opportunities.id", "opportunities.intake", "opportunities.location_scope"],
            name="fk_opportunity_versions_scope",
        ),
        CheckConstraint("version_number > 0", name="version_number"),
        CheckConstraint("jsonb_typeof(metadata) = 'object'", name="metadata_object"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"))
    version_number: Mapped[int] = mapped_column()
    cycle: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(Text)
    public_metadata: Mapped[OpportunityMetadata] = mapped_column(
        "metadata", ModelJson(OpportunityMetadata)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_txid: Mapped[str] = mapped_column(
        Text, server_default=text("pg_current_xact_id()::text")
    )


class VersionSourceRecord(Base):
    __tablename__ = "version_sources"
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("opportunity_versions.id"), primary_key=True
    )
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_snapshots.id"), primary_key=True, index=True
    )


def snapshot_record(snapshot: SourceSnapshot, *, text_object_key: str) -> SourceSnapshotRecord:
    """Preserve the validated MS-006 snapshot identity and first retrieval time."""
    snapshot = SourceSnapshot.model_validate(snapshot)
    return SourceSnapshotRecord(
        id=snapshot.source.snapshot_id,
        source_id=snapshot.source.id,
        raw_hash=snapshot.raw_file_hash,
        normalized_hash=snapshot.source.content_hash,
        normalized=snapshot.normalized,
        text_object_key=text_object_key,
        retrieved_at=snapshot.source.retrieved_at,
        authority=snapshot.source.authority,
        completeness=snapshot.source.completeness,
    )


def span_record(
    snapshot_id: UUID, normalized: NormalizedText, span: SourceSpan
) -> SourceSpanRecord:
    normalized.validate_span(span)
    return SourceSpanRecord(
        id=span.id,
        snapshot_id=snapshot_id,
        page=span.page,
        start=span.start,
        end=span.end,
        quote=span.quote,
    )
