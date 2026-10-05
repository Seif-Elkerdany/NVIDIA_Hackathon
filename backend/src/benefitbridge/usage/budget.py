"""Atomic bounded provider reservations; provider I/O never belongs in these transactions."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Self
from uuid import UUID, uuid4

from pydantic import Field, StrictInt, model_validator
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from benefitbridge.db.base import owner_transaction
from benefitbridge.db.budget import BudgetChargeRecord, BudgetLockRecord
from benefitbridge.db.jobs import UsageReservationRecord
from benefitbridge.domain.base import DomainModel, Sha256
from benefitbridge.domain.errors import DomainError
from benefitbridge.inference.registry import ModelRegistry, ModelSpec, Name
from benefitbridge.ports import ActorContext, Clock, ModelRole, ProviderUsage

MicroUsd = Annotated[StrictInt, Field(ge=0, le=2**63 - 1)]
Concurrency = Annotated[StrictInt, Field(ge=1, le=2**31 - 1)]
TokenLimit = Annotated[StrictInt, Field(ge=0, le=2**31 - 1)]


class BudgetLimits(DomainModel):
    """Every funded cap is explicit; deployment has no guessed global allowance."""

    run_microusd: MicroUsd
    owner_daily_microusd: MicroUsd
    global_daily_microusd: MicroUsd
    run_concurrency: Concurrency
    owner_concurrency: Concurrency
    global_concurrency: Concurrency


class CostQuote(DomainModel):
    """Frozen registry metadata and token bounds; estimated maximum, never a bill."""

    registry_version: Name
    registry_fingerprint: Sha256
    model: ModelSpec
    input_token_limit: TokenLimit
    output_token_limit: TokenLimit

    @model_validator(mode="after")
    def bounded_tokens(self) -> Self:
        if (
            self.output_token_limit > self.model.max_output_tokens
            or self.input_token_limit + self.output_token_limit > self.model.context_tokens
        ):
            raise ValueError("Call token bounds exceed configured model limits")
        return self

    @property
    def maximum_microusd(self) -> int:
        return self.model.cost_microusd(self.input_token_limit, self.output_token_limit)


def quote_model_call(
    registry: ModelRegistry,
    role: ModelRole,
    *,
    input_token_limit: int,
    output_token_limit: int | None = None,
) -> CostQuote:
    """Reuse MS-010 role resolution and Decimal ceiling, without provider I/O.

    Omitted output bounds reserve for the configured maximum output. Adapters
    must enforce these same bounds when they eventually obtain a reservation.
    Preflight readiness remains a separate required check before paid execution.
    """
    model = registry.resolve(role)
    return CostQuote(
        registry_version=registry.config.version,
        registry_fingerprint=registry.fingerprint,
        model=model,
        input_token_limit=input_token_limit,
        output_token_limit=model.max_output_tokens
        if output_token_limit is None
        else output_token_limit,
    )


class ProviderCostQuote(DomainModel):
    """Configured search/fetch cost ceiling; deployment supplies its price version."""

    provider: Name
    registry_version: Name
    price_version: Name
    maximum_microusd: MicroUsd


@dataclass(frozen=True)
class Reservation:
    id: UUID
    amount_microusd: int
    expires_at: datetime
    quote: CostQuote | ProviderCostQuote


class BudgetService:
    """Use ordinary private credentials + verified actor, or public-worker credentials.

    The constrained DB functions lock global → owner → run and see global monetary
    totals without exposing other owners' private rows. NULL billed cost is held
    across UTC day changes and account purge. Each retry/repair needs a new reserve.
    """

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        clock: Clock,
        limits: BudgetLimits,
        *,
        actor: ActorContext | None,
    ) -> None:
        self.sessions, self.clock, self.limits, self.actor = sessions, clock, limits, actor

    @staticmethod
    def _check(code: str, *, expected: set[str]) -> None:
        if code in expected:
            return
        status = (
            404
            if code == "NOT_FOUND"
            else 429
            if code in {"BUDGET_EXCEEDED", "CONCURRENCY_LIMIT"}
            else 409
        )
        raise DomainError(code, "Provider budget reservation is unavailable.", status)

    async def reserve(
        self,
        run_id: UUID | None,
        quote: CostQuote | ProviderCostQuote,
        *,
        timeout_seconds: int,
    ) -> Reservation:
        """Commit the maximum charge before starting any provider operation.

        Provider timeout must not exceed this reservation's expiry. The expiry
        frees an abandoned concurrency slot, while money remains conservatively held.
        """
        if (self.actor is None) != (run_id is None):
            raise ValueError("Private calls require a run; public maintenance has no owner/run")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 120:
            raise ValueError("Provider timeout must be between 1 and 120 seconds")
        if isinstance(quote, CostQuote) and timeout_seconds > quote.model.timeout_seconds:
            raise ValueError("Provider timeout exceeds the configured model limit")
        now = self.clock.now()
        if now.tzinfo is None or now.utcoffset() != timedelta(0):
            raise ValueError("Budget clock must return aware UTC time")
        amount = quote.maximum_microusd
        if amount > 2**63 - 1:
            raise ValueError("Configured reservation exceeds integer micro-USD range")
        reservation = Reservation(uuid4(), amount, now + timedelta(seconds=timeout_seconds), quote)
        metadata: dict[str, object]
        if isinstance(quote, CostQuote):
            metadata = {
                "registry_version": quote.registry_version,
                "registry_fingerprint": quote.registry_fingerprint,
                "price_version": quote.model.price_version,
                "provider": quote.model.provider,
                "model_id": quote.model.model_id,
                "input_token_limit": quote.input_token_limit,
                "output_token_limit": quote.output_token_limit,
            }
        else:
            metadata = {
                "registry_version": quote.registry_version,
                "price_version": quote.price_version,
                "provider": quote.provider,
            }
        parameters = {
            "id": reservation.id,
            "owner": self.actor.owner_id if self.actor else None,
            "run": run_id,
            "amount": amount,
            "quote": json.dumps(metadata),
            "limits": self.limits.model_dump_json(),
            "now": now,
            "expires": reservation.expires_at,
        }
        query = text(
            "SELECT public.benefitbridge_budget_reserve(:id,:owner,:run,:amount,"
            "CAST(:quote AS jsonb),CAST(:limits AS jsonb),:now,:expires)"
        )
        if self.actor is not None:
            async with owner_transaction(self.sessions, self.actor) as session:
                self._check(str(await session.scalar(query, parameters)), expected={"RESERVED"})
        else:
            async with self.sessions() as session, session.begin():
                self._check(str(await session.scalar(query, parameters)), expected={"RESERVED"})
        return reservation

    async def reconcile(self, reservation: Reservation, usage: ProviderUsage | None) -> None:
        """Record known billing or retain its entire hold when billing is uncertain.

        Known zero is explicit. Reporting a timeout with None does not refund
        money. Later reconciliation is idempotent; conflicting bills fail closed.
        An over-ceiling bill is recorded before returning COST_BOUND_EXCEEDED.
        """
        cost = usage.billed_microusd if usage is not None else None
        if cost is not None and (type(cost) is not int or not 0 <= cost <= 2**63 - 1):
            raise ValueError("Billing requires integer micro-USD")
        payload: dict[str, int] = {}
        if usage is not None:
            if any(
                type(count) is not int or not 0 <= count <= 2**31 - 1
                for count in (usage.input_tokens, usage.output_tokens)
            ):
                raise ValueError("Usage requires bounded integer token counts")
            payload = {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}
        now = self.clock.now().astimezone(UTC)
        query = text(
            "SELECT public.benefitbridge_budget_reconcile(:id,:cost,CAST(:usage AS jsonb),:now)"
        )
        parameters = {"id": reservation.id, "cost": cost, "usage": json.dumps(payload), "now": now}
        if self.actor is not None:
            async with owner_transaction(self.sessions, self.actor) as session:
                self._check(
                    str(await session.scalar(query, parameters)),
                    expected={"RECONCILED", "BILLING_UNKNOWN"},
                )
        else:
            async with self.sessions() as session, session.begin():
                self._check(
                    str(await session.scalar(query, parameters)),
                    expected={"RECONCILED", "BILLING_UNKNOWN"},
                )
        if cost is not None and cost > reservation.amount_microusd:
            raise DomainError(
                "COST_BOUND_EXCEEDED", "Provider charge exceeded its reserved ceiling.", 409
            )


class RetainedChargeReconciler:
    """Operator-only reconciliation of anonymous charges after private records are purged.

    Use the constrained budget role, never application or identity-administration
    credentials. A verified bill is required; elapsed time cannot refund a hold.
    """

    def __init__(self, sessions: async_sessionmaker[AsyncSession], clock: Clock) -> None:
        self.sessions, self.clock = sessions, clock

    async def reconcile(self, reservation_id: UUID, *, billed_microusd: int) -> None:
        if type(billed_microusd) is not int or not 0 <= billed_microusd <= 2**63 - 1:
            raise ValueError("Reconciliation requires verified integer micro-USD billing")
        async with self.sessions() as session, session.begin():
            permitted = await session.scalar(
                text(
                    "SELECT NOT (rolsuper OR rolbypassrls) AND "
                    "pg_has_role(current_user,'benefitbridge_budget_admin','member') AND NOT "
                    "pg_has_role(current_user,'benefitbridge_identity_admin','member') AND NOT "
                    "pg_has_role(current_user,'benefitbridge_app','member') AND NOT "
                    "pg_has_role(current_user,'benefitbridge_public_worker','member') "
                    "FROM pg_catalog.pg_roles WHERE rolname=current_user"
                )
            )
            if not permitted:
                raise RuntimeError("Retained charges require isolated budget-role credentials")
            await session.scalar(
                select(BudgetLockRecord).where(BudgetLockRecord.kind == "GLOBAL").with_for_update()
            )
            charge = await session.get(BudgetChargeRecord, reservation_id, with_for_update=True)
            if charge is None:
                raise DomainError("NOT_FOUND", "Retained charge is unavailable.", 404)
            if await session.get(UsageReservationRecord, reservation_id) is not None:
                raise DomainError(
                    "RECONCILIATION_CONFLICT", "Use the authorized run reconciliation path.", 409
                )
            if charge.cost is not None:
                if charge.cost != billed_microusd:
                    raise DomainError(
                        "RECONCILIATION_CONFLICT", "Charge is already reconciled.", 409
                    )
                return
            charge.cost = billed_microusd
            charge.settled_at = self.clock.now()
            charge.active = False
