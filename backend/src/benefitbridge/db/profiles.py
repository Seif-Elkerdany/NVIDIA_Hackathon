"""Typed identity tables. Publication services reuse MS-002 fact validation."""

from datetime import date, datetime
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from benefitbridge.db.base import Base
from benefitbridge.domain.enums import AccountStatus, FactAttribute, Provenance
from benefitbridge.domain.facts import FactValue

_fact_value: TypeAdapter[FactValue] = TypeAdapter(FactValue)


class FactValueJson(TypeDecorator[FactValue]):
    """The MS-002 tagged union remains the serialization/validation source."""

    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: FactValue | None, dialect: Dialect) -> object:
        if value is None:
            return None
        return _fact_value.dump_python(_fact_value.validate_python(value), mode="json")

    def process_result_value(self, value: object, dialect: Dialect) -> FactValue:
        return _fact_value.validate_python(value)


class AccountRecord(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'DELETING')", name="status"),
        CheckConstraint("deletion_epoch >= 0", name="deletion_epoch"),
        CheckConstraint("char_length(display_name) BETWEEN 1 AND 120", name="display_name"),
        CheckConstraint("(consent_version IS NULL) = (consent_at IS NULL)", name="consent_pair"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    status: Mapped[AccountStatus] = mapped_column(Enum(AccountStatus, native_enum=False, length=16))
    display_name: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(100))
    consent_version: Mapped[str | None] = mapped_column(String(100))
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    deletion_epoch: Mapped[int] = mapped_column(server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProfileRecord(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        UniqueConstraint("owner_id", name="uq_profiles_owner_id"),
        UniqueConstraint("owner_id", "id", name="uq_profiles_owner_id_id"),
        ForeignKeyConstraint(
            ["owner_id", "current_version_id"],
            ["profile_versions.owner_id", "profile_versions.id"],
            name="fk_profiles_current_version",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    current_version_id: Mapped[UUID] = mapped_column()


class ProfileVersionRecord(Base):
    __tablename__ = "profile_versions"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_profile_versions_owner_id_id"),
        UniqueConstraint(
            "owner_id", "version_number", name="uq_profile_versions_owner_id_version_number"
        ),
        CheckConstraint("version_number > 0", name="positive_version"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.owner_id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Only the transaction creating a version may assemble its membership.
    created_txid: Mapped[str] = mapped_column(
        Text, server_default=text("pg_current_xact_id()::text")
    )


class FactRecord(Base):
    __tablename__ = "facts"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_facts_owner_id_id"),
        UniqueConstraint("owner_id", "id", "attribute", name="uq_facts_owner_id_id_attribute"),
        CheckConstraint("jsonb_typeof(typed_value) = 'object'", name="value_object"),
        CheckConstraint(
            "provenance IN ('USER_CONFIRMED', 'USER_CONFIRMED_DOCUMENT', 'CONFLICTING')",
            name="provenance",
        ),
        CheckConstraint("conflict = (provenance = 'CONFLICTING')", name="conflict"),
        CheckConstraint(
            "valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from",
            name="validity",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    attribute: Mapped[FactAttribute] = mapped_column(
        Enum(
            FactAttribute,
            native_enum=False,
            length=100,
            values_callable=lambda enum: [member.value for member in enum],
        )
    )
    typed_value: Mapped[FactValue] = mapped_column(FactValueJson())
    provenance: Mapped[Provenance] = mapped_column(Enum(Provenance, native_enum=False, length=32))
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    conflict: Mapped[bool] = mapped_column(Boolean)


class ProfileVersionFactRecord(Base):
    __tablename__ = "profile_version_facts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_id", "version_id"],
            ["profile_versions.owner_id", "profile_versions.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["owner_id", "fact_id", "attribute"],
            ["facts.owner_id", "facts.id", "facts.attribute"],
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "owner_id",
            "version_id",
            "attribute",
            name="uq_profile_version_facts_owner_version_attribute",
        ),
    )
    owner_id: Mapped[UUID] = mapped_column(primary_key=True)
    version_id: Mapped[UUID] = mapped_column(primary_key=True)
    fact_id: Mapped[UUID] = mapped_column(primary_key=True)
    attribute: Mapped[FactAttribute] = mapped_column(
        Enum(
            FactAttribute,
            native_enum=False,
            length=100,
            values_callable=lambda enum: [member.value for member in enum],
        )
    )


class DeletedSubjectRecord(Base):
    __tablename__ = "deleted_subjects"
    __table_args__ = (
        CheckConstraint("octet_length(subject_hmac) = 32", name="hmac_length"),
        CheckConstraint("retain_until > deleted_at", name="retention"),
    )
    subject_hmac: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    retain_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
