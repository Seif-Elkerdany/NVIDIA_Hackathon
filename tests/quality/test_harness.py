import asyncio
import socket
import subprocess
import sys
from collections import deque
from datetime import timedelta
from pathlib import Path
from typing import Annotated
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from tests.fakes.providers import FIXED_NOW, FakeClock, FakeFetch, ScriptedLLM

from benefitbridge.composition import Dependencies, get_clock, get_llm
from benefitbridge.config import Settings
from benefitbridge.domain.dto import HealthLive
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import LLM, CallLimits, Clock, FetchRequest, LlmRequest, ModelRole

ROOT = Path(__file__).resolve().parents[2]


def llm_request() -> LlmRequest:
    return LlmRequest(
        ModelRole.FAST,
        "synthetic-model",
        "registry-1",
        "prompt-1",
        "Synthetic prompt",
        CallLimits(UUID(int=1), 1.0, 1, 1),
    )


def test_clock_is_injected_and_never_sleeps(fake_clock: FakeClock) -> None:
    assert fake_clock.now() == FIXED_NOW
    fake_clock.advance(2.5)
    assert fake_clock.now() == FIXED_NOW + timedelta(seconds=2.5)
    assert fake_clock.monotonic() == 2.5
    with pytest.raises(ValueError, match="backwards"):
        fake_clock.advance(-1)


def test_scripted_failure_and_recovery_preserve_actual_call_count() -> None:
    failure = DomainError("PROVIDER_FAILURE", "Synthetic timeout.", 503, retryable=True)
    adapter = ScriptedLLM(deque([failure, HealthLive(status="ok")]))

    async def scenario() -> None:
        with pytest.raises(DomainError) as caught:
            await adapter.generate(llm_request(), HealthLive)
        assert caught.value is failure
        response = await adapter.generate(llm_request(), HealthLive)
        assert response.value.status == "ok"
        assert response.usage.billed_microusd == 0
        assert len(adapter.calls) == 2
        with pytest.raises(AssertionError, match="exhausted"):
            await adapter.generate(llm_request(), HealthLive)

    asyncio.run(scenario())


def test_fetch_uses_injected_clock_and_rejects_oversize(fake_clock: FakeClock) -> None:
    url = "https://synthetic.example.invalid/source"
    adapter = FakeFetch(fake_clock, {url: b"synthetic"})

    async def scenario() -> None:
        request = FetchRequest(url, UUID(int=1), 20, 0, 1)
        first = await adapter.fetch(request)
        fake_clock.advance(5)
        second = await adapter.fetch(request)
        assert first.sha256 == second.sha256
        assert second.fetched_at == first.fetched_at + timedelta(seconds=5)
        with pytest.raises(DomainError):
            await adapter.fetch(FetchRequest(url, UUID(int=1), 1, 0, 1))

    asyncio.run(scenario())


@pytest.mark.parametrize("method", ["connect", "connect_ex", "sendto"])
def test_external_socket_paths_are_blocked_before_io(method: str) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        with pytest.raises(AssertionError, match="paid endpoints"):
            if method == "sendto":
                connection.sendto(b"synthetic", ("192.0.2.1", 443))
            else:
                getattr(connection, method)(("192.0.2.1", 443))


def test_external_dns_is_blocked_before_resolution() -> None:
    with pytest.raises(AssertionError, match="provider names"):
        socket.getaddrinfo("paid.synthetic.invalid", 443)


def test_paid_suite_cannot_be_enabled_in_ci() -> None:
    import os

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--suite",
            "live",
            "--allow-paid-live",
            "--live-budget-microusd",
            "1",
            "--collect-only",
        ],
        cwd=ROOT,
        env={**os.environ, "CI": "true"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 4
    assert "prohibited in ordinary CI" in result.stderr


@pytest.mark.integration
def test_in_process_api_uses_real_di_and_synthetic_ports(
    fake_dependencies: Dependencies, fixture_settings: Settings
) -> None:
    fake_dependencies.validate(fixture_settings)
    app = FastAPI()
    app.state.dependencies = fake_dependencies

    @app.get("/synthetic")
    async def endpoint(
        clock: Annotated[Clock, Depends(get_clock)], llm: Annotated[LLM, Depends(get_llm)]
    ) -> dict[str, str]:
        response = await llm.generate(llm_request(), HealthLive)
        return {"status": response.value.status, "at": clock.now().isoformat()}

    with TestClient(app) as client:
        assert client.get("/synthetic").json() == {"status": "ok", "at": FIXED_NOW.isoformat()}


@pytest.mark.integration
def test_compositions_do_not_share_mutable_provider_state() -> None:
    from tests.fakes.providers import fixture_dependencies

    first, second = fixture_dependencies(), fixture_dependencies()
    assert first.llm is not second.llm
    assert first.storage is not second.storage
    assert first.workflows is not second.workflows
