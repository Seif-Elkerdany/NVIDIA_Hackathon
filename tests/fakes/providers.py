"""Reusable deterministic provider scripts; no credentials, I/O or implicit fallback."""

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from math import isfinite
from typing import Literal

from tests.ports.fakes import FakeProfiles, FakeStorage, FakeTransactions, FakeWorkflows

from benefitbridge.composition import Dependencies
from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.dto import HealthLive
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import (
    LLM,
    Clock,
    Fetch,
    FetchedResource,
    FetchRequest,
    LlmRequest,
    LlmResponse,
    ProviderUsage,
    Search,
    SearchHit,
    SearchRequest,
)

FIXED_NOW = datetime(2026, 10, 4, 12, tzinfo=UTC)


@dataclass
class FakeClock:
    instant: datetime = FIXED_NOW
    elapsed: float = 0.0

    def __post_init__(self) -> None:
        if self.instant.utcoffset() != timedelta(0):
            raise ValueError("Fixture clocks require an aware UTC instant")
        if not isfinite(self.elapsed) or self.elapsed < 0:
            raise ValueError("Fixture elapsed time must be finite and nonnegative")

    def now(self) -> datetime:
        return self.instant

    def monotonic(self) -> float:
        return self.elapsed

    def advance(self, seconds: float) -> None:
        if not isfinite(seconds) or seconds < 0:
            raise ValueError("Fixture clocks cannot move backwards")
        self.instant += timedelta(seconds=seconds)
        self.elapsed += seconds


@dataclass
class ScriptedLLM:
    responses: deque[DomainModel | DomainError] = field(default_factory=deque)
    mode: Literal["fixture"] = "fixture"
    calls: list[tuple[str, str, str]] = field(default_factory=list)

    async def generate[T: DomainModel](
        self, request: LlmRequest, response_model: type[T]
    ) -> LlmResponse[T]:
        # Record version metadata only, never prompt text or credentials.
        self.calls.append((request.model_id, request.registry_version, request.prompt_version))
        if not self.responses:
            raise AssertionError("Synthetic LLM script exhausted; no live fallback")
        response = self.responses.popleft()
        if isinstance(response, DomainError):
            raise response
        value = response_model.model_validate(response.model_dump(mode="json"))
        return LlmResponse(value, ProviderUsage(1, 1, 0))


@dataclass
class FakeSearch:
    results: dict[str, tuple[SearchHit, ...]] = field(default_factory=dict)
    mode: Literal["fixture"] = "fixture"

    async def search(self, request: SearchRequest) -> tuple[SearchHit, ...]:
        if request.generalized_query not in self.results:
            raise AssertionError("Unregistered synthetic search; no live fallback")
        return self.results[request.generalized_query][: request.max_results]


@dataclass
class FakeFetch:
    clock: Clock
    resources: dict[str, bytes] = field(default_factory=dict)
    mode: Literal["fixture"] = "fixture"

    async def fetch(self, request: FetchRequest) -> FetchedResource:
        if request.url not in self.resources:
            raise AssertionError("Unregistered synthetic resource; no live fallback")
        body = self.resources[request.url]
        if len(body) > request.max_bytes:
            raise DomainError("PAYLOAD_TOO_LARGE", "Synthetic fetch exceeds its limit.", 413)
        return FetchedResource(
            request.url, "text/html", body, self.clock.now(), sha256(body).hexdigest()
        )


def fixture_dependencies(clock: FakeClock | None = None) -> Dependencies:
    """Fresh adapters per composition, using MS-003's existing repository/storage fakes."""
    clock = clock if clock is not None else FakeClock()
    llm: LLM = ScriptedLLM(deque([HealthLive(status="ok")]))
    search: Search = FakeSearch()
    fetch: Fetch = FakeFetch(clock)
    return Dependencies(
        clock=clock,
        provider_mode="fixture",
        llm=llm,
        search=search,
        fetch=fetch,
        storage=FakeStorage(),
        profiles=FakeProfiles(),
        workflows=FakeWorkflows(),
        transactions=FakeTransactions(),
    )
