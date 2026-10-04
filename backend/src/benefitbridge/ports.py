"""Typed boundaries for providers and durable work; no provider SDK or ambient state.

ActorContext comes from verified authentication or a persisted private job claim,
never a request body. Adapters perform I/O outside repository transactions. These
internal values are not a second public DTO catalog.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite
from types import TracebackType
from typing import Literal, Protocol, runtime_checkable
from uuid import UUID

from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.dto import ArtifactRef, DocumentDownload, Page, Run, RunEvent
from benefitbridge.domain.enums import RunKind, RunStatus


@dataclass(frozen=True)
class ActorContext:
    owner_id: UUID
    deletion_epoch: int
    request_id: str
    consent_version: str | None = None

    def __post_init__(self) -> None:
        if self.deletion_epoch < 0 or not 1 <= len(self.request_id) <= 64:
            raise ValueError("Invalid verified actor context")


class ModelRole(StrEnum):
    FAST = "FAST"
    REASON = "REASON"
    DEEP = "DEEP"


class JobScope(StrEnum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime:
        """Return an aware UTC instant."""
        ...

    def monotonic(self) -> float: ...


@dataclass(frozen=True)
class CallLimits:
    """A reservation is acquired by the budget service before adapter invocation."""

    reservation_id: UUID
    timeout_seconds: float
    max_input_tokens: int
    max_output_tokens: int

    def __post_init__(self) -> None:
        if (
            not isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
            or min(self.max_input_tokens, self.max_output_tokens) <= 0
        ):
            raise ValueError("Provider calls require positive time and token bounds")


@dataclass(frozen=True)
class LlmRequest:
    role: ModelRole
    model_id: str
    registry_version: str
    prompt_version: str
    prompt: str = field(repr=False)
    limits: CallLimits

    def __post_init__(self) -> None:
        if not all((self.model_id, self.registry_version, self.prompt_version, self.prompt)):
            raise ValueError("Inference requires a configured model and versioned prompt")


@dataclass(frozen=True)
class ProviderUsage:
    input_tokens: int
    output_tokens: int
    billed_microusd: int | None

    def __post_init__(self) -> None:
        if min(self.input_tokens, self.output_tokens) < 0 or (
            self.billed_microusd is not None and self.billed_microusd < 0
        ):
            raise ValueError("Provider usage cannot be negative")


@dataclass(frozen=True)
class LlmResponse[T: DomainModel]:
    value: T
    usage: ProviderUsage


@runtime_checkable
class LLM(Protocol):
    @property
    def mode(self) -> Literal["fixture", "real"]: ...

    async def generate[T: DomainModel](
        self, request: LlmRequest, response_model: type[T]
    ) -> LlmResponse[T]:
        """Validate structured output; no tool execution or implicit model fallback."""
        ...


@dataclass(frozen=True)
class SearchRequest:
    """Only a generalized, nonidentifying goal may cross this boundary."""

    generalized_query: str = field(repr=False)
    reservation_id: UUID
    max_results: int
    timeout_seconds: float

    def __post_init__(self) -> None:
        if not self.generalized_query.strip() or not 1 <= self.max_results <= 8:
            raise ValueError("Search requires a generalized query and at most eight hits")
        if not isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("Search requires a positive timeout")


@dataclass(frozen=True)
class SearchHit:
    url: str
    title: str
    snippet: str = field(repr=False)


@runtime_checkable
class Search(Protocol):
    @property
    def mode(self) -> Literal["fixture", "real"]: ...

    async def search(self, request: SearchRequest) -> tuple[SearchHit, ...]: ...


@dataclass(frozen=True)
class FetchRequest:
    url: str = field(repr=False)
    reservation_id: UUID
    max_bytes: int
    max_redirects: int
    timeout_seconds: float

    def __post_init__(self) -> None:
        if (
            self.max_bytes <= 0
            or self.max_redirects < 0
            or not isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise ValueError("Fetch requires bounded bytes, redirects and time")


@dataclass(frozen=True)
class FetchedResource:
    final_url: str = field(repr=False)
    media_type: str
    body: bytes = field(repr=False)
    fetched_at: datetime
    sha256: str


@runtime_checkable
class Fetch(Protocol):
    @property
    def mode(self) -> Literal["fixture", "real"]: ...

    async def fetch(self, request: FetchRequest) -> FetchedResource:
        """HTTPS/public targets only; validate DNS and every redirect before connecting."""
        ...


@dataclass(frozen=True)
class StorageObject:
    """Private storage keys are derived by the adapter, never supplied as filenames."""

    document_id: UUID
    version_id: UUID


@runtime_checkable
class Storage(Protocol):
    @property
    def mode(self) -> Literal["fixture", "real"]: ...

    async def put(
        self,
        actor: ActorContext,
        resource: StorageObject,
        chunks: AsyncIterator[bytes],
        max_bytes: int,
    ) -> None: ...

    async def read(self, actor: ActorContext, resource: StorageObject, max_bytes: int) -> bytes: ...

    async def delete(self, actor: ActorContext, resource: StorageObject) -> None: ...

    async def sign_download(
        self, actor: ActorContext, resource: StorageObject, expires_in: timedelta
    ) -> DocumentDownload:
        """Check active DB ownership and tombstones; expiry must not exceed five minutes."""
        ...


@runtime_checkable
class PrivateRepository[T: DomainModel](Protocol):
    async def get(self, actor: ActorContext, resource_id: UUID) -> T | None:
        """Filter by verified owner and tombstones, including historical artifacts."""
        ...

    async def list(self, actor: ActorContext, cursor: str | None, limit: int) -> Page[T]: ...

    async def add(self, actor: ActorContext, value: T) -> None:
        """Insert an immutable snapshot inside the caller's short transaction."""
        ...


@runtime_checkable
class PublicRepository[T: DomainModel](Protocol):
    async def get(self, resource_id: UUID) -> T | None: ...

    async def add(self, value: T) -> None:
        """Only the constrained ingestion/maintenance composition receives write access."""
        ...


@runtime_checkable
class WorkflowRepository(Protocol):
    async def get_run(self, actor: ActorContext, run_id: UUID) -> Run | None: ...

    async def events(
        self, actor: ActorContext, run_id: UUID, after_seq: int, limit: int
    ) -> tuple[RunEvent, ...]: ...

    async def publish(self, context: "StageContext", result: "StageResult") -> bool:
        """Atomically check lease fencing, current inputs and deletion epoch before publication.

        False means a stale claim; duplicates reuse the durable logical stage key.
        """
        ...


@runtime_checkable
class Transaction(Protocol):
    async def __aenter__(self) -> "Transaction": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


@runtime_checkable
class Transactions(Protocol):
    def begin(self, actor: ActorContext) -> Transaction:
        """Set transaction-local verified owner; never hold this across provider I/O."""
        ...


@dataclass(frozen=True)
class StageContext:
    job_id: UUID
    run_id: UUID | None
    kind: RunKind | None
    stage: str
    stage_key: str
    scope: JobScope
    actor: ActorContext | None
    fencing_token: int
    deadline_at: datetime
    inputs: DomainModel = field(repr=False)

    def __post_init__(self) -> None:
        if (self.scope == JobScope.PRIVATE) != (self.actor is not None):
            raise ValueError("Private work requires a verified actor; public work cannot carry one")
        if self.scope == JobScope.PRIVATE and (self.run_id is None or self.kind is None):
            raise ValueError("Private work requires a persisted run and kind")
        if not self.stage or not self.stage_key or self.fencing_token <= 0:
            raise ValueError("A claimed stage requires a durable key and positive fencing token")
        if self.deadline_at.utcoffset() != timedelta(0):
            raise ValueError("Stage deadlines must be aware UTC instants")


@dataclass(frozen=True)
class StageResult:
    status: RunStatus
    next_stage: str | None = None
    artifact_ref: ArtifactRef | None = None
    warning_codes: tuple[str, ...] = ()


@runtime_checkable
class StageHandler(Protocol):
    async def handle(self, context: StageContext) -> StageResult:
        """Bounded stage work; durable transitions go through the fenced repository."""
        ...
