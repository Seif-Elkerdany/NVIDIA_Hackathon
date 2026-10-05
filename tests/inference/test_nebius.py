"""Synthetic Nebius wire/ledger scenarios; network guard stays enabled throughout."""

import asyncio
import json
import logging
from dataclasses import replace
from datetime import timedelta
from uuid import UUID

import httpx2
import pytest
from pydantic import ConfigDict, Field, SecretStr, StrictBool
from tests.fakes.providers import FakeClock, ScriptedLLM
from tests.inference.test_registry import model, registry, report

from benefitbridge.composition import Dependencies
from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.errors import DomainError
from benefitbridge.inference.nebius import (
    AdapterLimits,
    BudgetedInference,
    InferenceTask,
    NebiusLLM,
    ProviderFailure,
    bind_nebius,
)
from benefitbridge.ports import LLM, ModelRole, ProviderUsage
from benefitbridge.usage.budget import CostQuote, ProviderCostQuote, Reservation

SECRET = "synthetic-private-api-key"
PRIVATE = "synthetic-email@example.invalid /private/document"
NOW = FakeClock().now()


class Answer(DomainModel):
    ok: StrictBool


def task(**changes):
    return InferenceTask(
        **{
            "role": ModelRole.FAST,
            "prompt_version": "synthetic-v1",
            "prompt": PRIVATE,
            "max_input_tokens": 1024,
            "max_output_tokens": 128,
            "timeout_seconds": 5,
        }
        | changes
    )


def completion(content='{"ok":true}', **changes):
    return {
        "model": "synthetic-reason",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": content,
                    "reasoning_content": "synthetic-hidden-chain-never-persist",
                },
            }
        ],
        "usage": {"prompt_tokens": 20, "completion_tokens": 8},
    } | changes


class Ledger:
    """Isolated MS-019 protocol fake; uncertain charges are held, never fabricated bills."""

    def __init__(self, clock, events, max_calls=2):
        self.clock, self.events, self.max_calls = clock, events, max_calls
        self.reservations = []
        self.entries = []

    async def reserve(
        self, run_id: UUID | None, quote: CostQuote | ProviderCostQuote, *, timeout_seconds: int
    ) -> Reservation:
        if len(self.reservations) >= self.max_calls:
            raise DomainError("BUDGET_EXCEEDED", "Synthetic allowance exhausted.", 429)
        value = Reservation(
            UUID(int=len(self.reservations) + 1),
            quote.maximum_microusd,
            self.clock.now() + timedelta(seconds=timeout_seconds),
            quote,
        )
        self.reservations.append(value)
        self.events.append("reserve")
        return value

    async def reconcile(self, reservation: Reservation, usage: ProviderUsage | None) -> None:
        self.events.append("reconcile")
        self.entries.append((reservation, usage))


def setup(handler, *, clock=None, limits=None, counter=None, current=None, evidence=None):
    clock = clock or FakeClock()
    current = current or registry(model())
    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    llm = NebiusLLM(
        current,
        evidence or report(current),
        clock,
        client,
        SecretStr(SECRET),
        counter or (lambda spec, payload: 100),
        limits=limits,
    )
    return llm, client


def test_protocol_binding_uses_the_same_boundary_as_fakes_and_resolved_role():
    async def scenario():
        calls = []

        def handler(request):
            payload = json.loads(request.content)
            calls.append(payload)
            assert request.url == model().endpoint
            assert request.headers["authorization"] == "Bearer " + SECRET
            assert request.headers["accept-encoding"] == "identity"
            assert payload["model"] == "synthetic-reason"
            assert payload["max_completion_tokens"] == 128
            assert payload["stream"] is False and payload["n"] == 1
            assert "tools" not in payload and "logprobs" not in payload
            assert payload["response_format"]["json_schema"]["strict"] is True
            data = json.loads(payload["messages"][1]["content"])
            assert data == {"task_data": PRIVATE}
            return httpx2.Response(200, json=completion())

        llm, client = setup(handler)
        assert isinstance(llm, LLM) and isinstance(ScriptedLLM(), LLM)
        deps = bind_nebius(Dependencies(clock=llm.clock), llm)
        assert deps.llm is llm and deps.provider_mode == "real"
        async with client:
            response = await deps.llm.generate(task().request(llm.registry), Answer)
        assert response.value.ok and response.usage.billed_microusd is None
        assert len(calls) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "invalid",
    [
        "{",
        "```json\n{}\n```",
        '{"ok":false,"ok":true}',
        '{"ok":true,"hidden":"private"}',
        '{"ok":"true"}',
        '{"ok":NaN}',
        "[true]",
    ],
)
def test_one_repair_is_newly_reserved_with_no_raw_response_or_reasoning(invalid):
    async def scenario():
        events, payloads = [], []

        def handler(request):
            events.append("http")
            payloads.append(json.loads(request.content))
            return httpx2.Response(
                200, json=completion(invalid if len(payloads) == 1 else '{"ok":true}')
            )

        llm, client = setup(handler)
        ledger = Ledger(llm.clock, events)
        async with client:
            response = await BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                task(), Answer, total_timeout_seconds=10
            )
        assert response.value.ok
        assert (response.usage.input_tokens, response.usage.output_tokens) == (40, 16)
        assert events == ["reserve", "http", "reconcile", "reserve", "http", "reconcile"]
        assert len({entry.id for entry in ledger.reservations}) == 2
        assert all(entry[1].billed_microusd is None for entry in ledger.entries)
        assert payloads[1]["messages"][1] == payloads[0]["messages"][1]
        assert "previous response did not validate" in payloads[1]["messages"][0]["content"]
        assert "synthetic-hidden-chain" not in json.dumps(payloads[1])

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "max_calls,repair,expected,calls",
    [
        (2, True, "SCHEMA_INVALID", 2),
        (1, True, "BUDGET_EXCEEDED", 1),
        (2, False, "SCHEMA_INVALID", 1),
    ],
)
def test_invalid_answers_stop_after_one_repair_or_budget_denial(max_calls, repair, expected, calls):
    async def scenario():
        events = []

        def handler(request):
            events.append("http")
            return httpx2.Response(200, json=completion("{"))

        llm, client = setup(handler)
        ledger = Ledger(llm.clock, events, max_calls)
        with pytest.raises(DomainError) as caught:
            async with client:
                await BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                    task(), Answer, total_timeout_seconds=10, allow_repair=repair
                )
        assert caught.value.code == expected
        assert events.count("http") == calls == len(ledger.entries)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "status,code,retry",
    [
        (429, "RATE_LIMITED", True),
        (503, "PROVIDER_UNAVAILABLE", True),
        (404, "MODEL_UNAVAILABLE", False),
        (401, "PROVIDER_UNAVAILABLE", False),
        (400, "SCHEMA_UNSUPPORTED", False),
        (302, "PROVIDER_UNAVAILABLE", False),
    ],
)
def test_http_errors_fail_without_unfunded_retry_or_following_redirect(status, code, retry):
    async def scenario():
        events = []

        def handler(request):
            events.append("http")
            return httpx2.Response(
                status,
                text=SECRET + PRIVATE,
                headers={"retry-after": "120", "location": "https://evil.invalid/"},
            )

        llm, client = setup(handler)
        ledger = Ledger(llm.clock, events)
        with pytest.raises(ProviderFailure) as caught:
            async with client:
                await BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                    task(), Answer, total_timeout_seconds=10
                )
        assert caught.value.code == code and caught.value.retryable is retry
        assert caught.value.retry_after_seconds == 120
        assert SECRET not in str(caught.value) and PRIVATE not in repr(caught.value)
        assert events == ["reserve", "http", "reconcile"]
        assert ledger.entries[0][1] is None

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "document,expected",
    [
        (
            completion(choices=[{"finish_reason": "length", "message": {"content": "{"}}]),
            "TRUNCATED_RESPONSE",
        ),
        (completion(model="missing-model"), "INVALID_RESPONSE"),
        (completion(usage={"prompt_tokens": True, "completion_tokens": 8}), "INVALID_RESPONSE"),
        (completion(usage={"prompt_tokens": 1025, "completion_tokens": 8}), "TOKEN_LIMIT_EXCEEDED"),
        (completion(usage={"prompt_tokens": 20, "completion_tokens": 129}), "TOKEN_LIMIT_EXCEEDED"),
        (
            completion(
                choices=[
                    {"finish_reason": "stop", "message": {"content": "{}", "tool_calls": [{}]}}
                ]
            ),
            "UNSUPPORTED_RESPONSE",
        ),
        (
            completion(
                choices=[
                    {"finish_reason": "stop", "message": {"content": None, "refusal": PRIVATE}}
                ]
            ),
            "UNSUPPORTED_RESPONSE",
        ),
        (completion(usage=None), "INVALID_RESPONSE"),
        (completion(usage={"prompt_tokens": 2**40, "completion_tokens": 8}), "INVALID_RESPONSE"),
    ],
)
def test_truncation_usage_mismatch_and_tool_output_cannot_be_repaired(document, expected):
    async def scenario():
        events = []

        def handler(request):
            events.append("http")
            return httpx2.Response(200, json=document)

        llm, client = setup(handler)
        ledger = Ledger(llm.clock, events)
        with pytest.raises(ProviderFailure) as caught:
            async with client:
                await BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                    task(), Answer, total_timeout_seconds=10
                )
        assert caught.value.code == expected
        assert len(ledger.entries) == events.count("http") == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "counter,limits,changes,code",
    [
        (lambda spec, payload: 1025, None, {}, "TOKEN_LIMIT_EXCEEDED"),
        (lambda spec, payload: True, None, {}, "TOKEN_LIMIT_EXCEEDED"),
        (None, AdapterLimits(max_request_bytes=100), {}, "INPUT_LIMIT_EXCEEDED"),
        (None, AdapterLimits(max_schema_bytes=10), {}, "SCHEMA_UNSUPPORTED"),
        (None, None, {"max_output_tokens": 129}, "TOKEN_LIMIT_EXCEEDED"),
        (None, None, {"timeout_seconds": 6}, "TOKEN_LIMIT_EXCEEDED"),
        (None, None, {"max_input_tokens": 4096}, "TOKEN_LIMIT_EXCEEDED"),
    ],
)
def test_bounds_fail_before_any_charge_or_http(counter, limits, changes, code):
    async def scenario():
        def forbidden(request):
            pytest.fail("The provider must not be invoked")

        llm, client = setup(forbidden, counter=counter, limits=limits)
        ledger = Ledger(llm.clock, [])
        with pytest.raises(ProviderFailure) as caught:
            async with client:
                await BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                    task(**changes), Answer, total_timeout_seconds=10
                )
        assert caught.value.code == code and not ledger.reservations

    asyncio.run(scenario())


def test_missing_models_stale_preflight_registry_change_and_unsafe_schemas_fail_closed():
    class Thought(DomainModel):
        chain_of_thought: str

    class Open(DomainModel):
        model_config = ConfigDict(extra="allow")
        ok: bool

    class External(DomainModel):
        ok: bool = Field(json_schema_extra={"$ref": "https://private.invalid/schema"})

    async def scenario():
        def forbidden(request):
            pytest.fail("No provider call")

        llm, client = setup(forbidden)
        async with client:
            for response_model in (Thought, Open, External):
                with pytest.raises(ProviderFailure) as caught:
                    llm.prepare(task().request(llm.registry), response_model)
                assert caught.value.code == "SCHEMA_UNSUPPORTED"
            with pytest.raises(DomainError):
                task(role=ModelRole.DEEP).request(llm.registry)
            with pytest.raises(ProviderFailure, match="could not complete"):
                llm.prepare(replace(task().request(llm.registry), model_id="other"), Answer)
            llm.clock.advance(3600)
            with pytest.raises(ProviderFailure) as caught:
                llm.prepare(task().request(llm.registry), Answer)
            assert caught.value.code == "PREFLIGHT_REQUIRED"

    asyncio.run(scenario())


@pytest.mark.parametrize("kind", ["timeout", "connection", "cancel", "total-timeout"])
def test_uncertain_attempt_and_cancellation_are_reconciled_without_refund(kind):
    async def scenario():
        events = []
        started = asyncio.Event()

        async def handler(request):
            events.append("http")
            started.set()
            if kind == "timeout":
                raise httpx2.ReadTimeout(SECRET + PRIVATE, request=request)
            if kind == "connection":
                raise httpx2.ConnectError(SECRET + PRIVATE, request=request)
            await asyncio.Event().wait()

        llm, client = setup(handler)
        ledger = Ledger(llm.clock, events)
        async with client:
            operation = asyncio.create_task(
                BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                    task(), Answer, total_timeout_seconds=1 if kind == "total-timeout" else 10
                )
            )
            await started.wait()
            if kind == "cancel":
                operation.cancel()
            with pytest.raises(asyncio.CancelledError if kind == "cancel" else ProviderFailure):
                await operation
        assert events == ["reserve", "http", "reconcile"]
        assert ledger.entries[0][1] is None

    asyncio.run(scenario())


def test_redacted_metadata_does_not_include_secrets_prompts_outputs_or_chain(caplog):
    async def scenario():
        def handler(request):
            return httpx2.Response(200, json=completion())

        llm, client = setup(handler)
        async with client:
            result = await llm.generate(task().request(llm.registry), Answer)
        assert result.value.model_dump() == {"ok": True}
        assert "synthetic-hidden-chain" not in repr(result)

    with caplog.at_level(logging.INFO, logger="benefitbridge.inference.nebius"):
        asyncio.run(scenario())
    serialized = "\n".join(str(record.__dict__) for record in caplog.records)
    for secret in (SECRET, PRIVATE, "synthetic-hidden-chain", '{"ok":true}'):
        assert secret not in serialized
    assert "schema_hash" in serialized and "input_tokens" in serialized


@pytest.mark.parametrize(
    "body,headers,limit,code",
    [
        (b"{", {"content-type": "application/json"}, 1024, "INVALID_RESPONSE"),
        (b"html-private", {"content-type": "text/html"}, 1024, "INVALID_RESPONSE"),
        (
            json.dumps(completion()).encode(),
            {"content-type": "application/json"},
            16,
            "RESPONSE_LIMIT_EXCEEDED",
        ),
        (
            b"anything",
            {"content-type": "application/json", "content-encoding": "br"},
            1024,
            "UNSUPPORTED_RESPONSE",
        ),
    ],
)
def test_bounded_response_and_media_type(body, headers, limit, code):
    async def scenario():
        llm, client = setup(
            lambda request: httpx2.Response(200, content=body, headers=headers),
            limits=AdapterLimits(max_response_bytes=limit),
        )
        with pytest.raises(ProviderFailure) as caught:
            async with client:
                await llm.generate(task().request(llm.registry), Answer)
        assert caught.value.code == code

    asyncio.run(scenario())


def test_five_retryable_failures_open_circuit_and_allow_one_funded_cooldown_probe():
    async def scenario():
        calls = []
        started, release = asyncio.Event(), asyncio.Event()

        async def handler(request):
            calls.append(request)
            if len(calls) <= 5:
                return httpx2.Response(429)
            started.set()
            await release.wait()
            return httpx2.Response(200, json=completion())

        llm, client = setup(handler)
        ledger = Ledger(llm.clock, [], max_calls=10)
        funded = BudgetedInference(llm, ledger, run_id=UUID(int=100))
        async with client:
            for _ in range(5):
                with pytest.raises(ProviderFailure) as caught:
                    await funded.infer(task(), Answer, total_timeout_seconds=10)
                assert caught.value.code == "RATE_LIMITED"
            for seconds in (0, 59):
                llm.clock.advance(seconds)
                with pytest.raises(ProviderFailure) as caught:
                    await funded.infer(task(), Answer, total_timeout_seconds=10)
                assert caught.value.code == "CIRCUIT_OPEN"
            assert len(ledger.reservations) == len(calls) == 5
            llm.clock.advance(1)
            probe = asyncio.create_task(funded.infer(task(), Answer, total_timeout_seconds=10))
            await started.wait()
            with pytest.raises(ProviderFailure) as caught:
                await funded.infer(task(), Answer, total_timeout_seconds=10)
            assert caught.value.code == "CIRCUIT_OPEN"
            assert len(ledger.reservations) == len(calls) == 6
            release.set()
            assert (await probe).value.ok
            assert (await funded.infer(task(), Answer, total_timeout_seconds=10)).value.ok

    asyncio.run(scenario())


def test_repair_respects_remaining_deadline_and_never_uses_previous_answer():
    async def scenario():
        calls, events = [], []
        clock = FakeClock()

        def handler(request):
            calls.append(request)
            clock.advance(4.5)
            return httpx2.Response(200, json=completion("{"))

        llm, client = setup(handler, clock=clock)
        ledger = Ledger(clock, events)
        async with client:
            with pytest.raises(ProviderFailure) as caught:
                await BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                    task(), Answer, total_timeout_seconds=5
                )
        assert caught.value.code == "PROVIDER_TIMEOUT"
        assert len(calls) == len(ledger.reservations) == len(ledger.entries) == 1

    asyncio.run(scenario())


def test_expired_reservation_never_starts_http_and_reconciles_explicit_zero():
    async def scenario():
        clock = FakeClock()

        def forbidden(request):
            pytest.fail("An expired reservation cannot fund a provider call")

        class SlowLedger(Ledger):
            async def reserve(self, run_id, quote, *, timeout_seconds):
                value = await super().reserve(run_id, quote, timeout_seconds=timeout_seconds)
                clock.advance(timeout_seconds)
                return value

        llm, client = setup(forbidden, clock=clock)
        ledger = SlowLedger(clock, [])
        async with client:
            with pytest.raises(ProviderFailure) as caught:
                await BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                    task(), Answer, total_timeout_seconds=10
                )
        assert caught.value.code == "PROVIDER_TIMEOUT"
        assert ledger.entries[0][1] == ProviderUsage(0, 0, 0)

    asyncio.run(scenario())


def test_missing_registry_fixture_preflight_and_counter_failure_do_not_spend():
    async def scenario():
        def forbidden(request):
            pytest.fail("No provider call")

        def failed_counter(spec, payload):
            raise ValueError(SECRET + PRIVATE)

        for current, counter, evidence, code in (
            (registry(), None, None, "DEPENDENCY_UNAVAILABLE"),
            (registry(model()), failed_counter, None, "TOKEN_COUNTER_UNAVAILABLE"),
            (
                registry(model()),
                None,
                report(registry(model()), mode="fixture"),
                "PREFLIGHT_REQUIRED",
            ),
        ):
            llm, client = setup(forbidden, current=current, counter=counter, evidence=evidence)
            ledger = Ledger(llm.clock, [])
            async with client:
                with pytest.raises(DomainError) as caught:
                    await BudgetedInference(llm, ledger, run_id=UUID(int=100)).infer(
                        task(), Answer, total_timeout_seconds=10
                    )
            assert caught.value.code == code and not ledger.reservations
            assert SECRET not in str(caught.value)

    asyncio.run(scenario())
