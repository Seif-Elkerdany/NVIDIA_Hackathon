import asyncio
from dataclasses import replace
from datetime import timedelta
from typing import Annotated
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from benefitbridge.composition import (
    Dependencies,
    HandlerBinding,
    get_actor,
    get_clock,
    get_dependencies,
    get_llm,
    resolve_handler,
)
from benefitbridge.config import ConfigurationError, Settings
from benefitbridge.domain.dto import HealthLive, Profile
from benefitbridge.domain.enums import RunKind, RunStatus
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import (
    ActorContext,
    CallLimits,
    Clock,
    FetchRequest,
    JobScope,
    LlmRequest,
    ModelRole,
    ProviderUsage,
    SearchRequest,
    StageContext,
    StorageObject,
)

from .fakes import (
    NOW,
    FakeClock,
    FakeProfiles,
    FakeStage,
    FakeStorage,
    FakeTransactions,
    FakeWorkflows,
    fixture_dependencies,
)

ACTOR = ActorContext(UUID(int=1), 0, "synthetic-request")


def stage_context():
    return StageContext(
        job_id=UUID(int=2),
        run_id=UUID(int=3),
        kind=RunKind.EVALUATE,
        stage="EVALUATE",
        stage_key="evaluate-v1",
        scope=JobScope.PRIVATE,
        actor=ACTOR,
        fencing_token=1,
        deadline_at=NOW + timedelta(minutes=1),
        inputs=HealthLive(status="ok"),
    )


def test_fixture_adapters_have_typed_deterministic_outputs():
    async def check():
        dependencies = fixture_dependencies()
        dependencies.validate(Settings(_env_file=None, app_env="test", provider_mode="fixture"))
        assert dependencies.llm is not None
        assert dependencies.search is not None
        assert dependencies.fetch is not None
        request = LlmRequest(
            ModelRole.FAST,
            "synthetic-model",
            "registry-1",
            "prompt-1",
            "private fixture text",
            CallLimits(UUID(int=4), 5, 20, 10),
        )
        first = await dependencies.llm.generate(request, HealthLive)
        assert first == await dependencies.llm.generate(request, HealthLive)
        assert first.value == HealthLive(status="ok")
        assert first.usage.billed_microusd == 0
        assert "private fixture text" not in repr(request)
        hits = await dependencies.search.search(
            SearchRequest("research internships", UUID(int=4), 8, 5)
        )
        fetched = await dependencies.fetch.fetch(FetchRequest(hits[0].url, UUID(int=4), 100, 2, 5))
        assert fetched.fetched_at == NOW
        assert dependencies.clock.now() == NOW
        assert dependencies.clock.monotonic() == 100.0

    asyncio.run(check())


def test_named_dependency_can_be_overridden_in_an_isolated_router():
    app = FastAPI()
    app.state.dependencies = Dependencies(clock=FakeClock())

    @app.get("/synthetic")
    def synthetic(clock: Annotated[Clock, Depends(get_clock)]):
        return {"instant": clock.now().isoformat()}

    replacement = FakeClock(NOW + timedelta(days=1))
    app.dependency_overrides[get_clock] = lambda: replacement
    with TestClient(app) as client:
        assert client.get("/synthetic").json() == {"instant": replacement.now().isoformat()}


def test_unavailable_dependency_does_not_return_a_success_fake():
    app = FastAPI()
    app.state.dependencies = Dependencies()
    request = Request({"type": "http", "app": app})
    with pytest.raises(DomainError) as caught:
        get_llm(request)
    assert caught.value.code == "DEPENDENCY_UNAVAILABLE"
    assert caught.value.status == 503


def test_actor_is_taken_only_from_verified_request_state():
    app = FastAPI()
    request = Request({"type": "http", "app": app, "headers": [(b"owner_id", b"1")]})
    with pytest.raises(DomainError, match="Authentication"):
        get_actor(request)
    request.state.actor = ACTOR
    assert get_actor(request) is ACTOR


def test_untyped_dependencies_are_rejected():
    app = FastAPI()
    app.state.dependencies = object()
    with pytest.raises(ConfigurationError, match="not been composed"):
        get_dependencies(Request({"type": "http", "app": app}))
    with pytest.raises(ConfigurationError, match="Invalid dependency binding"):
        Dependencies(llm=object())


def test_synchronous_callable_cannot_be_bound_as_an_async_stage_handler():
    class WrongStage:
        def handle(self, context):
            return None

    with pytest.raises(ConfigurationError, match="Stage handler must implement"):
        Dependencies(handlers={"EVALUATE": HandlerBinding(WrongStage())})


def test_fixtures_cannot_be_bound_as_real_providers(production_settings):
    dependencies = replace(fixture_dependencies(), provider_mode="real")
    with pytest.raises(ConfigurationError, match="Adapter mode"):
        dependencies.validate(production_settings)


def test_disabled_mode_cannot_run_bound_providers():
    with pytest.raises(ConfigurationError, match="explicit provider mode"):
        fixture_dependencies().validate(Settings(_env_file=None))


def test_production_requires_explicit_complete_dependencies(production_settings):
    with pytest.raises(ConfigurationError, match="explicit real adapter"):
        Dependencies().validate(production_settings)
    with pytest.raises(ConfigurationError, match="Missing production dependencies"):
        Dependencies(provider_mode="real").validate(production_settings)


def test_handler_map_is_frozen_and_public_claims_cannot_resolve_private_handlers():
    original = {"EVALUATE": HandlerBinding(FakeStage())}
    dependencies = Dependencies(handlers=original)
    original.clear()
    assert resolve_handler(dependencies, "EVALUATE", JobScope.PRIVATE)
    with pytest.raises(ConfigurationError, match="job scope"):
        resolve_handler(dependencies, "EVALUATE", JobScope.PUBLIC)
    with pytest.raises(ConfigurationError, match="missing"):
        resolve_handler(dependencies, "arbitrary", JobScope.PRIVATE)
    with pytest.raises(TypeError):
        dependencies.handlers["injected"] = HandlerBinding(FakeStage())


@pytest.mark.parametrize(
    "changes",
    [
        {"actor": None},
        {"scope": JobScope.PUBLIC},
        {"run_id": None},
        {"fencing_token": 0},
        {"stage_key": ""},
        {"deadline_at": NOW.replace(tzinfo=None)},
    ],
)
def test_claim_context_rejects_missing_authority_and_fencing(changes):
    with pytest.raises(ValueError):
        replace(stage_context(), **changes)


def test_public_context_has_no_private_actor():
    context = replace(stage_context(), scope=JobScope.PUBLIC, actor=None, run_id=None, kind=None)
    assert context.actor is None


def test_repository_storage_and_stage_fakes_use_the_ports():
    async def chunks():
        yield b"synthetic"

    async def check():
        storage = FakeStorage()
        resource = StorageObject(UUID(int=5), UUID(int=6))
        await storage.put(ACTOR, resource, chunks(), 20)
        assert await storage.read(ACTOR, resource, 20) == b"synthetic"
        foreign = replace(ACTOR, owner_id=UUID(int=99))
        with pytest.raises(DomainError, match="unavailable"):
            await storage.read(foreign, resource, 20)
        with pytest.raises(ValueError, match="expiry"):
            await storage.sign_download(ACTOR, resource, timedelta(minutes=6))
        signed = await storage.sign_download(ACTOR, resource, timedelta(minutes=5))
        assert signed.expires_at == NOW + timedelta(minutes=5)
        profiles = FakeProfiles()
        profile = Profile(
            id=UUID(int=7), version_id=UUID(int=8), version_number=1, facts=(), updated_at=NOW
        )
        await profiles.add(ACTOR, profile)
        assert await profiles.get(ACTOR, profile.id) == profile
        assert await profiles.get(foreign, profile.id) is None
        transaction = FakeTransactions().begin(ACTOR)
        async with transaction:
            await transaction.commit()
        context = stage_context()
        result = await FakeStage().handle(context)
        assert result.status == RunStatus.SUCCEEDED
        workflows = FakeWorkflows()
        assert await workflows.publish(context, result)
        assert await workflows.publish(context, result)
        assert len(workflows.published) == 1
        assert not await workflows.publish(replace(context, fencing_token=2), result)
        await storage.delete(ACTOR, resource)
        assert not storage.objects

    asyncio.run(check())


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_provider_limits_cannot_be_unbounded(timeout):
    with pytest.raises(ValueError):
        CallLimits(UUID(int=4), timeout, 20, 10)
    with pytest.raises(ValueError):
        SearchRequest("generalized goal", UUID(int=4), 8, timeout)
    with pytest.raises(ValueError):
        FetchRequest("https://synthetic.example.invalid", UUID(int=4), 100, 2, timeout)


def test_unknown_billing_is_distinct_from_zero():
    assert ProviderUsage(1, 1, None) != ProviderUsage(1, 1, 0)
