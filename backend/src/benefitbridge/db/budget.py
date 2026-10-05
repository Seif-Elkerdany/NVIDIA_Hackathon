"""Budget locks and non-content billing journal that survives private account purge."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from benefitbridge.db.base import Base


class BudgetLockRecord(Base):
    __tablename__ = "budget_locks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_id", "run_id"], ["runs.owner_id", "runs.id"], ondelete="CASCADE"
        ),
        CheckConstraint(
            "(kind = 'GLOBAL' AND key = '00000000-0000-0000-0000-000000000000'::uuid "
            "AND owner_id IS NULL AND run_id IS NULL) OR "
            "(kind = 'OWNER' AND key = owner_id AND owner_id IS NOT NULL AND run_id IS NULL) OR "
            "(kind = 'RUN' AND key = run_id AND owner_id IS NOT NULL AND run_id IS NOT NULL)",
            name="scope",
        ),
    )
    kind: Mapped[str] = mapped_column(String(6), primary_key=True)
    key: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    run_id: Mapped[UUID | None] = mapped_column()


class BudgetChargeRecord(Base):
    """No owner/run FK, text, prompt or provider request ID is retained here."""

    __tablename__ = "budget_charges"
    __table_args__ = (
        CheckConstraint("amount >= 0 AND (cost IS NULL OR cost >= 0)", name="money"),
        CheckConstraint("expires_at > created_at", name="expiry"),
        CheckConstraint("(cost IS NULL) = (settled_at IS NULL)", name="settlement"),
        CheckConstraint("NOT active OR cost IS NULL", name="active"),
        CheckConstraint("jsonb_typeof(quote) = 'object'", name="quote"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    cost: Mapped[int | None] = mapped_column(BigInteger)
    active: Mapped[bool] = mapped_column(Boolean)
    quote: Mapped[dict[str, object]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
