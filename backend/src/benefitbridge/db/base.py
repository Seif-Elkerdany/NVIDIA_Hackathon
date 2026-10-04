"""PostgreSQL tenancy primitives; callers supply only verified ActorContext values."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from hashlib import sha256
from hmac import new as hmac_new
from uuid import UUID

from sqlalchemy import MetaData, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import ActorContext


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def subject_hmac(subject: UUID, key: bytes) -> bytes:
    """Minimal deny-ledger key; the configured key must survive backup restores."""
    if len(key) < 32:
        raise ValueError("Deletion HMAC key must contain at least 32 bytes")
    return hmac_new(key, b"benefitbridge:deleted-subject:v1:" + subject.bytes, sha256).digest()


async def set_owner_context(session: AsyncSession, actor: ActorContext) -> None:
    """SET LOCAL equivalent, parameterized and scoped to an existing transaction.

    Never call this with request-body identity or a migration/service-role session.
    A session must not change actors mid-transaction.
    """
    if not session.in_transaction():
        raise RuntimeError("Owner context requires an explicit transaction")
    role = (
        await session.execute(
            text(
                "SELECT rolsuper OR rolbypassrls FROM pg_catalog.pg_roles "
                "WHERE rolname = current_user"
            )
        )
    ).scalar_one()
    if role:
        raise RuntimeError("Private application transactions require a role without RLS bypass")
    if (
        await session.execute(
            text("SELECT pg_has_role(current_user, 'benefitbridge_identity_admin', 'member')")
        )
    ).scalar_one():
        raise RuntimeError(
            "Private application transactions cannot use identity-administration roles"
        )
    existing = (
        await session.execute(text("SELECT nullif(current_setting('app.owner_id', true), '')"))
    ).scalar_one()
    if existing is not None and existing != str(actor.owner_id):
        raise RuntimeError("A transaction cannot change its verified owner")
    existing_epoch = (
        await session.execute(
            text("SELECT nullif(current_setting('app.deletion_epoch', true), '')")
        )
    ).scalar_one()
    if existing_epoch is not None and existing_epoch != str(actor.deletion_epoch):
        raise RuntimeError("A transaction cannot change its verified deletion epoch")
    await session.execute(
        text(
            "SELECT set_config('app.owner_id', :owner, true), "
            "set_config('app.deletion_epoch', :epoch, true)"
        ),
        {"owner": str(actor.owner_id), "epoch": str(actor.deletion_epoch)},
    )


@asynccontextmanager
async def owner_transaction(
    sessions: async_sessionmaker[AsyncSession], actor: ActorContext
) -> AsyncIterator[AsyncSession]:
    """Lock account first to fence deletion; services lock other rows afterwards.

    No provider calls belong in this short transaction. Bootstrap before an
    account exists is the separate identity-administration path in MS-008.
    """
    from benefitbridge.db.profiles import AccountRecord
    from benefitbridge.domain.enums import AccountStatus

    async with sessions() as session, session.begin():
        await set_owner_context(session, actor)
        account = (
            await session.execute(
                select(AccountRecord.id)
                .where(
                    AccountRecord.id == actor.owner_id,
                    AccountRecord.status == AccountStatus.ACTIVE,
                    AccountRecord.deletion_epoch == actor.deletion_epoch,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if account is None:
            raise DomainError("NOT_FOUND", "Account is unavailable", 404)
        yield session
