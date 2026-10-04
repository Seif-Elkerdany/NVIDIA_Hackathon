"""Explicit dependency injection and stage bindings shared by API and workers.

MS-003 defines the composition boundary. Real adapters are installed by their
owning sprints; missing dependencies never become implicit fixture adapters.
"""

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from inspect import iscoroutinefunction
from types import MappingProxyType
from typing import Literal

from fastapi import Request

from benefitbridge.config import ConfigurationError, Settings
from benefitbridge.domain.dto import Profile
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import (
    LLM,
    ActorContext,
    Clock,
    Fetch,
    JobScope,
    PrivateRepository,
    Search,
    StageHandler,
    Storage,
    Transactions,
    WorkflowRepository,
)


@dataclass(frozen=True)
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()


@dataclass(frozen=True)
class HandlerBinding:
    handler: StageHandler
    scope: JobScope = JobScope.PRIVATE


@dataclass(frozen=True)
class Dependencies:
    clock: Clock = field(default_factory=SystemClock)
    provider_mode: Literal["disabled", "fixture", "real"] = "disabled"
    llm: LLM | None = None
    search: Search | None = None
    fetch: Fetch | None = None
    storage: Storage | None = None
    profiles: PrivateRepository[Profile] | None = None
    workflows: WorkflowRepository | None = None
    transactions: Transactions | None = None
    handlers: Mapping[str, HandlerBinding] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Freeze a copy so readiness cannot be invalidated by a caller mutating its dict.
        object.__setattr__(self, "handlers", MappingProxyType(dict(self.handlers)))
        if not isinstance(self.clock, Clock):
            raise ConfigurationError("Clock must implement its protocol")
        for name, protocol in (
            ("llm", LLM),
            ("search", Search),
            ("fetch", Fetch),
            ("storage", Storage),
            ("profiles", PrivateRepository),
            ("workflows", WorkflowRepository),
            ("transactions", Transactions),
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(value, protocol):
                raise ConfigurationError(f"Invalid dependency binding: {name}")
        for name, binding in self.handlers.items():
            if not name or not isinstance(binding, HandlerBinding):
                raise ConfigurationError("Invalid stage handler binding")
            if not isinstance(binding.handler, StageHandler) or not iscoroutinefunction(
                binding.handler.handle
            ):
                raise ConfigurationError(f"Stage handler must implement its protocol: {name}")

    def validate(self, settings: Settings) -> None:
        providers = (self.llm, self.search, self.fetch, self.storage)
        if any(provider is not None for provider in providers):
            if self.provider_mode == "disabled" or self.provider_mode != settings.provider_mode:
                raise ConfigurationError("Provider bindings do not match explicit provider mode")
            if any(
                provider is not None and provider.mode != self.provider_mode
                for provider in providers
            ):
                raise ConfigurationError("Adapter mode does not match explicit provider mode")
        if settings.app_env == "production":
            if self.provider_mode != "real":
                raise ConfigurationError("Production requires explicit real adapter bindings")
            missing = [
                name
                for name in (
                    "llm",
                    "search",
                    "fetch",
                    "storage",
                    "profiles",
                    "workflows",
                    "transactions",
                )
                if getattr(self, name) is None
            ]
            if missing:
                raise ConfigurationError("Missing production dependencies: " + ", ".join(missing))


def build_dependencies(settings: Settings) -> Dependencies:
    """No SDK construction, network calls or automatic test fake selection."""
    return Dependencies(provider_mode=settings.provider_mode)


def get_dependencies(request: Request) -> Dependencies:
    dependencies = getattr(request.app.state, "dependencies", None)
    if not isinstance(dependencies, Dependencies):
        raise ConfigurationError("Application dependencies have not been composed")
    return dependencies


def get_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if not isinstance(settings, Settings):
        raise ConfigurationError("Application settings have not been composed")
    return settings


def get_actor(request: Request) -> ActorContext:
    """Auth owns verification; this dependency never trusts headers/body owner IDs."""
    actor = getattr(request.state, "actor", None)
    if not isinstance(actor, ActorContext):
        raise DomainError("UNAUTHENTICATED", "Authentication is required.", 401)
    return actor


def _require[T](value: T | None, name: str) -> T:
    if value is None:
        raise DomainError(
            "DEPENDENCY_UNAVAILABLE", f"The {name} service is unavailable.", 503, True
        )
    return value


def get_clock(request: Request) -> Clock:
    return get_dependencies(request).clock


def get_llm(request: Request) -> LLM:
    return _require(get_dependencies(request).llm, "inference")


def get_search(request: Request) -> Search:
    return _require(get_dependencies(request).search, "search")


def get_fetch(request: Request) -> Fetch:
    return _require(get_dependencies(request).fetch, "fetch")


def get_storage(request: Request) -> Storage:
    return _require(get_dependencies(request).storage, "storage")


def get_profiles(request: Request) -> PrivateRepository[Profile]:
    return _require(get_dependencies(request).profiles, "profile repository")


def get_workflows(request: Request) -> WorkflowRepository:
    return _require(get_dependencies(request).workflows, "workflow repository")


def get_transactions(request: Request) -> Transactions:
    return _require(get_dependencies(request).transactions, "transaction")


def resolve_handler(dependencies: Dependencies, name: str, scope: JobScope) -> StageHandler:
    """Public maintenance cannot resolve private handlers through a payload key."""
    binding = dependencies.handlers.get(name)
    if binding is None or binding.scope != scope:
        raise ConfigurationError("Stage handler is missing or incompatible with job scope")
    return binding.handler
