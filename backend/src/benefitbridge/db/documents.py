"""Private document versions, page evidence and immutable fact support (MS-025)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from benefitbridge.db.base import Base
from benefitbridge.db.profiles import FactValueJson
from benefitbridge.db.sources import ModelJson
from benefitbridge.domain.enums import DocumentKind, DocumentQuality, DocumentStatus
from benefitbridge.domain.facts import FactCandidate, FactValue
from benefitbridge.sources.contracts import NormalizedText


class DocumentRecord(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_documents_owner_id_id"),
        ForeignKeyConstraint(
            ["owner_id", "current_version_id", "id"],
            ["document_versions.owner_id", "document_versions.id", "document_versions.document_id"],
            name="fk_documents_current_version",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        CheckConstraint(
            "bytes_reserved BETWEEN 1 AND 10485760 AND size_bytes >= 0 "
            "AND size_bytes <= bytes_reserved",
            name="quota_bytes",
        ),
        CheckConstraint(
            "revision > 0 AND updated_at >= created_at AND upload_expires_at > created_at",
            name="revision_times",
        ),
        CheckConstraint("char_length(filename) BETWEEN 1 AND 120", name="filename"),
        CheckConstraint("sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$'", name="hash"),
        CheckConstraint("deleted_at IS NULL OR status = 'DELETING'", name="tombstone"),
        Index("ix_documents_owner_created", "owner_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(120))
    kind: Mapped[DocumentKind] = mapped_column(
        Enum(DocumentKind, native_enum=False, create_constraint=True)
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, create_constraint=True)
    )
    bytes_reserved: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    sha256: Mapped[str | None] = mapped_column(String(64))
    current_version_id: Mapped[UUID | None] = mapped_column()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    upload_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DocumentVersionRecord(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_document_versions_owner_id_id"),
        UniqueConstraint("owner_id", "id", "document_id", name="uq_document_versions_document"),
        UniqueConstraint(
            "owner_id", "document_id", "version_number", name="uq_document_versions_number"
        ),
        ForeignKeyConstraint(
            ["owner_id", "document_id"], ["documents.owner_id", "documents.id"], ondelete="CASCADE"
        ),
        CheckConstraint("version_number > 0 AND page_count BETWEEN 1 AND 20", name="bounds"),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="hash"),
        CheckConstraint(
            "char_length(object_key) BETWEEN 1 AND 512 AND object_key !~ '(^/|\\.\\.)'",
            name="object_key",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    version_number: Mapped[int] = mapped_column(Integer)
    object_key: Mapped[str] = mapped_column(String(512))
    content_hash: Mapped[str] = mapped_column(String(64))
    normalized: Mapped[NormalizedText] = mapped_column(ModelJson(NormalizedText))
    page_count: Mapped[int] = mapped_column(Integer)
    quality: Mapped[DocumentQuality] = mapped_column(
        Enum(DocumentQuality, native_enum=False, create_constraint=True)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EvidenceSpanRecord(Base):
    __tablename__ = "evidence_spans"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_evidence_spans_owner_id_id"),
        ForeignKeyConstraint(
            ["owner_id", "document_version_id", "document_id"],
            ["document_versions.owner_id", "document_versions.id", "document_versions.document_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            'page BETWEEN 1 AND 20 AND start >= 0 AND "end" > start '
            'AND char_length(quote) = "end" - start',
            name="span",
        ),
        CheckConstraint("normalized_hash ~ '^[0-9a-f]{64}$'", name="hash"),
        Index("ix_evidence_spans_owner_document", "owner_id", "document_version_id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    document_version_id: Mapped[UUID] = mapped_column()
    page: Mapped[int] = mapped_column(Integer)
    start: Mapped[int] = mapped_column(Integer)
    end: Mapped[int] = mapped_column(Integer)
    quote: Mapped[str] = mapped_column(Text)
    normalized_hash: Mapped[str] = mapped_column(String(64))


class FactCandidateRecord(Base):
    __tablename__ = "fact_candidates"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_fact_candidates_owner_id_id"),
        ForeignKeyConstraint(
            ["owner_id", "document_id"], ["documents.owner_id", "documents.id"], ondelete="CASCADE"
        ),
        CheckConstraint("revision > 0", name="revision"),
        Index("ix_fact_candidates_owner_document", "owner_id", "document_id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    candidate: Mapped[FactCandidate] = mapped_column(ModelJson(FactCandidate))
    revision: Mapped[int] = mapped_column(server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FactEvidenceRecord(Base):
    __tablename__ = "fact_evidence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_id", "fact_id"], ["facts.owner_id", "facts.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["owner_id", "evidence_id"],
            ["evidence_spans.owner_id", "evidence_spans.id"],
            ondelete="CASCADE",
        ),
    )
    owner_id: Mapped[UUID] = mapped_column(primary_key=True)
    fact_id: Mapped[UUID] = mapped_column(primary_key=True)
    evidence_id: Mapped[UUID] = mapped_column(primary_key=True)
    # Matching is verified by the review/edit service; the exact confirmed value
    # is retained so support cannot be transferred to a different qualification.
    supported_value: Mapped[FactValue] = mapped_column(FactValueJson())
    independently_confirmed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
