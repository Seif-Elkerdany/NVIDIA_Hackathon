"""Validated cost quotation and operator limits for MS-019.

These pure interfaces do not authorize provider calls or reserve funds. Durable
reservation enforcement requires global accounting that survives private purge;
the current MS-015 schema does not provide that persistence contract.
"""

from typing import Annotated, Self

from pydantic import Field, StrictInt, model_validator

from benefitbridge.domain.base import DomainModel, Sha256
from benefitbridge.inference.registry import ModelRegistry, ModelSpec, Name
from benefitbridge.ports import ModelRole

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
