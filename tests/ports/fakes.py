"""Deterministic protocol implementations used only by isolated MS-003 tests."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from types import TracebackType
from typing import Literal
from uuid import UUID

from benefitbridge.composition import Dependencies, HandlerBinding
from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.dto import DocumentDownload, HealthLive, Page, Profile, Run, RunEvent
from benefitbridge.domain.enums import RunStatus
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import (
    LLM,
    ActorContext,
    Clock,
    Fetch,
    FetchedResource,
    FetchRequest,
    LlmRequest,
    LlmResponse,
    PrivateRepository,
    ProviderUsage,
    PublicRepository,
    Search,
    SearchHit,
    SearchRequest,
    StageContext,
    StageHandler,
    StageResult,
    Storage,
    StorageObject,
    Transaction,
    Transactions,
    WorkflowRepository,
)

NOW = datetime(2026, 10, 4, 12, tzinfo=UTC)


@dataclass(frozen=True)
class FakeClock:
    instant: datetime = NOW
    elapsed: float = 100.0

    def now(self) -> datetime:
        return self.instant

    def monotonic(self) -> float:
        return self.elapsed


@dataclass(frozen=True)
class FakeLLM:
    seed: DomainModel = field(default_factory=lambda: HealthLive(status="ok"))
    mode: Literal["fixture"] = "fixture"

    async def generate[T: DomainModel](
        self, request: LlmRequest, response_model: type[T]
    ) -> LlmResponse[T]:
        value = response_model.model_validate(self.seed.model_dump(mode="json"))
        return LlmResponse(value, ProviderUsage(1, 1, 0))


@dataclass(frozen=True)
class FakeSearch:
    mode: Literal["fixture"] = "fixture"

    async def search(self, request: SearchRequest) -> tuple[SearchHit, ...]:
        return (
            SearchHit("https://synthetic.example.invalid/program", "Synthetic program", "Fixture"),
        )


@dataclass(frozen=True)
class FakeFetch:
    mode: Literal["fixture"] = "fixture"

    async def fetch(self, request: FetchRequest) -> FetchedResource:
        body = b"<p>Synthetic source</p>"[: request.max_bytes]
        return FetchedResource(request.url, "text/html", body, NOW, sha256(body).hexdigest())


@dataclass
class FakeStorage:
    mode: Literal["fixture"] = "fixture"
    objects: dict[tuple[UUID, StorageObject], bytes] = field(default_factory=dict)

    async def put(
        self,
        actor: ActorContext,
        resource: StorageObject,
        chunks: AsyncIterator[bytes],
        max_bytes: int,
    ) -> None:
        body = bytearray()
        async for chunk in chunks:
            body.extend(chunk)
            if len(body) > max_bytes:
                raise DomainError("PAYLOAD_TOO_LARGE", "Upload exceeds its limit.", 413)
        self.objects[actor.owner_id, resource] = bytes(body)

    async def read(self, actor: ActorContext, resource: StorageObject, max_bytes: int) -> bytes:
        body = self.objects.get((actor.owner_id, resource))
        if body is None:
            raise DomainError("NOT_FOUND", "Object unavailable.", 404)
        if len(body) > max_bytes:
            raise DomainError("PAYLOAD_TOO_LARGE", "Download exceeds its limit.", 413)
        return body

    async def delete(self, actor: ActorContext, resource: StorageObject) -> None:
        self.objects.pop((actor.owner_id, resource), None)

    async def sign_download(
        self, actor: ActorContext, resource: StorageObject, expires_in: timedelta
    ) -> DocumentDownload:
        if not timedelta(0) < expires_in <= timedelta(minutes=5):
            raise ValueError("Invalid expiry")
        await self.read(actor, resource, 10 * 1024 * 1024)
        return DocumentDownload(
            url="https://synthetic.example.invalid/download", expires_at=NOW + expires_in
        )


@dataclass
class FakeProfiles:
    records: dict[tuple[UUID, UUID], Profile] = field(default_factory=dict)

    async def get(self, actor: ActorContext, resource_id: UUID) -> Profile | None:
        return self.records.get((actor.owner_id, resource_id))

    async def list(self, actor: ActorContext, cursor: str | None, limit: int) -> Page[Profile]:
        values = tuple(
            value for (owner, _), value in self.records.items() if owner == actor.owner_id
        )
        return Page(items=values[:limit], next_cursor=None)

    async def add(self, actor: ActorContext, value: Profile) -> None:
        self.records[actor.owner_id, value.id] = value


@dataclass
class FakePublic:
    records: dict[UUID, HealthLive] = field(default_factory=dict)

    async def get(self, resource_id: UUID) -> HealthLive | None:
        return self.records.get(resource_id)

    async def add(self, value: HealthLive) -> None:
        self.records[UUID(int=1)] = value


@dataclass
class FakeWorkflows:
    current_fence: int = 1
    published: dict[tuple[UUID | None, str], StageResult] = field(default_factory=dict)

    async def get_run(self, actor: ActorContext, run_id: UUID) -> Run | None:
        return None

    async def events(
        self, actor: ActorContext, run_id: UUID, after_seq: int, limit: int
    ) -> tuple[RunEvent, ...]:
        return ()

    async def publish(self, context: StageContext, result: StageResult) -> bool:
        if context.fencing_token != self.current_fence:
            return False
        self.published.setdefault((context.run_id, context.stage_key), result)
        return True


@dataclass
class FakeTransaction:
    committed: bool = False
    rolled_back: bool = False

    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self.committed:
            await self.rollback()

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


@dataclass(frozen=True)
class FakeTransactions:
    def begin(self, actor: ActorContext) -> Transaction:
        return FakeTransaction()


@dataclass(frozen=True)
class FakeStage:
    async def handle(self, context: StageContext) -> StageResult:
        return StageResult(RunStatus.SUCCEEDED)


# These assignments are checked by mypy, so runtime structural checks cannot
# hide an incorrect async signature, argument type or model return type.
clock: Clock = FakeClock()
llm: LLM = FakeLLM()
search: Search = FakeSearch()
fetch: Fetch = FakeFetch()
storage: Storage = FakeStorage()
profiles: PrivateRepository[Profile] = FakeProfiles()
public: PublicRepository[HealthLive] = FakePublic()
workflows: WorkflowRepository = FakeWorkflows()
transactions: Transactions = FakeTransactions()
stage: StageHandler = FakeStage()


def fixture_dependencies() -> Dependencies:
    return Dependencies(
        clock=clock,
        provider_mode="fixture",
        llm=llm,
        search=search,
        fetch=fetch,
        storage=storage,
        profiles=profiles,
        workflows=workflows,
        transactions=transactions,
        handlers={"EVALUATE": HandlerBinding(stage)},
    )
