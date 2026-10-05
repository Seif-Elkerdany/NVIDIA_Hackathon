"""Bounded Nebius structured inference and MS-019-funded single repair.

``generate`` implements the pre-reserved MS-003 LLM port with one HTTP attempt.
``BudgetedInference.infer`` is the usable run-scoped composition for reserving
each attempt, including at most one repair. Neither path runs automatic HTTP
retries, executes tools, records prompts, or mistakes price estimates for bills.
"""

import asyncio
import json
import logging
import math
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from email.utils import parsedate_to_datetime
from hashlib import sha256
from typing import Literal, Protocol
from uuid import UUID

import httpx2
from pydantic import JsonValue, SecretStr, ValidationError

from benefitbridge.composition import Dependencies
from benefitbridge.config import ConfigurationError
from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.errors import DomainError
from benefitbridge.inference.prompts import POLICY_VERSION, REPAIR_POLICY, SYSTEM_POLICY
from benefitbridge.inference.registry import ModelRegistry, ModelSpec, PreflightReport
from benefitbridge.ports import (
    LLM,
    CallLimits,
    Clock,
    LlmRequest,
    LlmResponse,
    ModelRole,
    ProviderUsage,
)
from benefitbridge.usage.budget import CostQuote, ProviderCostQuote, Reservation, quote_model_call

logger = logging.getLogger(__name__)
TokenCounter = Callable[[ModelSpec, dict[str, JsonValue]], int]


class Budget(Protocol):
    async def reserve(
        self,
        run_id: UUID | None,
        quote: CostQuote | ProviderCostQuote,
        *,
        timeout_seconds: int,
    ) -> Reservation: ...

    async def reconcile(self, reservation: Reservation, usage: ProviderUsage | None) -> None: ...


@dataclass(frozen=True)
class AdapterLimits:
    max_request_bytes: int = 65_536
    max_response_bytes: int = 1_048_576
    max_schema_bytes: int = 32_768

    def __post_init__(self) -> None:
        if any(type(value) is not int or value <= 0 for value in vars(self).values()):
            raise ValueError("Inference byte limits must be positive integers")


class ProviderFailure(DomainError):
    """Only safe codes, counts and bounded retry metadata cross this boundary."""

    def __init__(
        self,
        code: str,
        *,
        retryable: bool = False,
        usage: ProviderUsage | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(code, "Structured inference could not complete.", 503, retryable)
        self.usage = usage
        self.retry_after_seconds = retry_after_seconds


def _json(raw: bytes | str) -> JsonValue:
    def unique(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
        result: dict[str, JsonValue] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError("Nonfinite JSON number")

    try:
        value: JsonValue = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise ProviderFailure("INVALID_RESPONSE") from None


def _object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ProviderFailure("INVALID_RESPONSE")
    return value


def _schema[T: DomainModel](response_model: type[T], limits: AdapterLimits) -> dict[str, JsonValue]:
    try:
        schema: dict[str, JsonValue] = response_model.model_json_schema()
        encoded = json.dumps(schema).encode()
    except (ValueError, TypeError, RecursionError):
        raise ProviderFailure("SCHEMA_UNSUPPORTED") from None
    if (
        response_model.model_config.get("extra") != "forbid"
        or schema.get("type") != "object"
        or len(encoded) > limits.max_schema_bytes
    ):
        raise ProviderFailure("SCHEMA_UNSUPPORTED")

    def inspect(value: JsonValue, depth: int = 0) -> None:
        if depth > 32:
            raise ProviderFailure("SCHEMA_UNSUPPORTED")
        if isinstance(value, dict):
            reference = value.get("$ref")
            if reference is not None and (
                not isinstance(reference, str) or not reference.startswith("#/$defs/")
            ):
                raise ProviderFailure("SCHEMA_UNSUPPORTED")
            properties = value.get("properties")
            if isinstance(properties, dict) and any(
                name.lower() in {"chain_of_thought", "reasoning_content", "hidden_reasoning"}
                for name in properties
            ):
                raise ProviderFailure("SCHEMA_UNSUPPORTED")
            if any(
                name in value
                for name in ("unevaluatedProperties", "patternProperties", "$dynamicRef")
            ):
                raise ProviderFailure("SCHEMA_UNSUPPORTED")
            for child in value.values():
                inspect(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                inspect(child, depth + 1)

    inspect(schema)
    return schema


class NebiusLLM:
    """One charged attempt. The caller owns the reservation and reconciliation.

    token_counter must be a verified local counter for the configured model,
    including chat-template/schema overhead. No guessed tokenizer is installed.
    The injected client must not contain retrying transports or logging hooks
    that record private request/response bodies; production uses a normal client.
    """

    def __init__(
        self,
        registry: ModelRegistry,
        preflight: PreflightReport,
        clock: Clock,
        client: httpx2.AsyncClient,
        api_key: SecretStr,
        token_counter: TokenCounter,
        *,
        limits: AdapterLimits | None = None,
    ) -> None:
        secret = api_key.get_secret_value()
        if not 1 <= len(secret) <= 4096 or any(not 33 <= ord(char) <= 126 for char in secret):
            raise ConfigurationError("Nebius credentials must be configured")
        self.registry, self.preflight, self.clock = registry, preflight, clock
        self.client, self._key, self._counter = client, api_key, token_counter
        self.limits = limits or AdapterLimits()
        self._retry_failures = 0
        self._circuit_until = 0.0
        self._probing = False

    @property
    def mode(self) -> Literal["real"]:
        return "real"

    def prepare[T: DomainModel](
        self, request: LlmRequest, response_model: type[T], *, repair: bool = False
    ) -> tuple[ModelSpec, dict[str, JsonValue]]:
        self._available()
        model = self.registry.resolve(request.role)
        readiness = self.registry.readiness(self.clock, self.preflight)
        if not readiness.inference_available or (
            request.role.value == "DEEP" and not readiness.deep_available
        ):
            raise ProviderFailure("PREFLIGHT_REQUIRED")
        if (
            model.model_id != request.model_id
            or self.registry.config.version != request.registry_version
        ):
            raise ProviderFailure("REGISTRY_CHANGED")
        if not model.json_schema:
            raise ProviderFailure("SCHEMA_UNSUPPORTED")
        if (
            type(request.limits.max_input_tokens) is not int
            or type(request.limits.max_output_tokens) is not int
            or request.limits.max_output_tokens > model.max_output_tokens
            or request.limits.max_input_tokens + request.limits.max_output_tokens
            > model.context_tokens
            or request.limits.timeout_seconds > model.timeout_seconds
        ):
            raise ProviderFailure("TOKEN_LIMIT_EXCEEDED")
        schema = _schema(response_model, self.limits)
        payload: dict[str, JsonValue] = {
            "model": model.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_POLICY + (" " + REPAIR_POLICY if repair else ""),
                },
                # JSON encoding supplies an unambiguous data boundary without copying responses.
                {"role": "user", "content": json.dumps({"task_data": request.prompt})},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "benefitbridge_result", "strict": True, "schema": schema},
            },
            "max_completion_tokens": request.limits.max_output_tokens,
            "stream": False,
            "n": 1,
        }
        if len(json.dumps(payload).encode()) > self.limits.max_request_bytes:
            raise ProviderFailure("INPUT_LIMIT_EXCEEDED")
        try:
            tokens = self._counter(model, payload)
        except (ValueError, TypeError, LookupError):
            raise ProviderFailure("TOKEN_COUNTER_UNAVAILABLE") from None
        if type(tokens) is not int or not 0 <= tokens <= request.limits.max_input_tokens:
            raise ProviderFailure("TOKEN_LIMIT_EXCEEDED")
        return model, payload

    async def generate[T: DomainModel](
        self, request: LlmRequest, response_model: type[T]
    ) -> LlmResponse[T]:
        model, payload = self.prepare(request, response_model)
        return await self._generate(request, response_model, model, payload)

    async def _generate[T: DomainModel](
        self,
        request: LlmRequest,
        response_model: type[T],
        model: ModelSpec,
        payload: dict[str, JsonValue],
    ) -> LlmResponse[T]:
        self._available()
        probe = self._circuit_until > 0
        if probe:
            self._probing = True
        started = self.clock.monotonic()
        registry_fingerprint = self.registry.fingerprint
        retry_failure = False
        code = "SUCCEEDED"
        usage: ProviderUsage | None = None
        try:
            async with asyncio.timeout(request.limits.timeout_seconds):
                async with self.client.stream(
                    "POST",
                    model.endpoint,
                    headers={
                        "Authorization": f"Bearer {self._key.get_secret_value()}",
                        "Accept-Encoding": "identity",
                    },
                    json=payload,
                    timeout=request.limits.timeout_seconds,
                    follow_redirects=False,
                ) as response:
                    if response.status_code != 200:
                        retry = response.status_code == 429 or response.status_code in {
                            500,
                            502,
                            503,
                            504,
                        }
                        error = (
                            "RATE_LIMITED"
                            if response.status_code == 429
                            else "MODEL_UNAVAILABLE"
                            if response.status_code == 404
                            else "SCHEMA_UNSUPPORTED"
                            if response.status_code in {400, 422}
                            else "PROVIDER_UNAVAILABLE"
                        )
                        raise ProviderFailure(
                            error, retryable=retry, retry_after_seconds=self._retry_after(response)
                        )
                    if (
                        response.headers.get("content-type", "").split(";", 1)[0].strip()
                        != "application/json"
                    ):
                        raise ProviderFailure("INVALID_RESPONSE")
                    if response.headers.get("content-encoding", "identity") != "identity":
                        raise ProviderFailure("UNSUPPORTED_RESPONSE")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(body) + len(chunk) > self.limits.max_response_bytes:
                            raise ProviderFailure("RESPONSE_LIMIT_EXCEEDED")
                        body.extend(chunk)
                    document = _object(_json(bytes(body)))
                    counts = _object(document.get("usage"))
                    inputs, outputs = counts.get("prompt_tokens"), counts.get("completion_tokens")
                    if (
                        type(inputs) is not int
                        or type(outputs) is not int
                        or not 0 <= inputs <= 2**31 - 1
                        or not 0 <= outputs <= 2**31 - 1
                    ):
                        raise ProviderFailure("INVALID_RESPONSE")
                    # Token usage is measured; billing is not supplied by this API response.
                    usage = ProviderUsage(inputs, outputs, None)
                    if (
                        inputs > request.limits.max_input_tokens
                        or outputs > request.limits.max_output_tokens
                    ):
                        raise ProviderFailure("TOKEN_LIMIT_EXCEEDED", usage=usage)
                    choices = document.get("choices")
                    if (
                        document.get("model") != model.model_id
                        or not isinstance(choices, list)
                        or len(choices) != 1
                    ):
                        raise ProviderFailure("INVALID_RESPONSE", usage=usage)
                    choice = _object(choices[0])
                    message = _object(choice.get("message"))
                    if choice.get("finish_reason") == "length":
                        raise ProviderFailure("TRUNCATED_RESPONSE", usage=usage)
                    if (
                        choice.get("finish_reason") != "stop"
                        or message.get("tool_calls")
                        or message.get("refusal")
                    ):
                        raise ProviderFailure("UNSUPPORTED_RESPONSE", usage=usage)
                    content = message.get("content")
                    if not isinstance(content, str):
                        raise ProviderFailure("INVALID_RESPONSE", usage=usage)
                    try:
                        _json(content)
                        value = response_model.model_validate_json(content)
                    except (ValidationError, ProviderFailure):
                        raise ProviderFailure("SCHEMA_INVALID", usage=usage) from None
                    return LlmResponse(value, usage)
        except (TimeoutError, httpx2.TimeoutException):
            retry_failure = True
            code = "PROVIDER_TIMEOUT"
            raise ProviderFailure(code, retryable=True, usage=usage) from None
        except httpx2.HTTPError:
            retry_failure = True
            code = "PROVIDER_UNAVAILABLE"
            raise ProviderFailure(code, retryable=True, usage=usage) from None
        except asyncio.CancelledError:
            code = "CANCELLED"
            raise
        except ProviderFailure as failure:
            code = failure.code
            retry_failure = failure.retryable
            if failure.usage is None:
                failure.usage = usage
            raise
        finally:
            self._probing = False if probe else self._probing
            if retry_failure:
                self._retry_failures += 1
                if self._retry_failures >= 5 or probe:
                    self._circuit_until = self.clock.monotonic() + 60
            elif code == "SUCCEEDED":
                self._retry_failures = 0
                self._circuit_until = 0.0
            elif not probe:
                self._retry_failures = 0
            logger.info(
                "inference_attempt",
                extra={
                    "event_code": code,
                    "reservation_id": str(request.limits.reservation_id),
                    "registry_fingerprint": registry_fingerprint,
                    "model_hash": sha256(model.model_id.encode()).hexdigest(),
                    "prompt_version_hash": sha256(
                        (POLICY_VERSION + request.prompt_version).encode()
                    ).hexdigest(),
                    "schema_hash": sha256(
                        json.dumps(payload["response_format"], sort_keys=True).encode()
                    ).hexdigest(),
                    "duration_ms": max(0, int((self.clock.monotonic() - started) * 1000)),
                    "input_tokens": usage.input_tokens if usage else None,
                    "output_tokens": usage.output_tokens if usage else None,
                },
            )

    def _available(self) -> None:
        remaining = self._circuit_until - self.clock.monotonic()
        if remaining > 0 or self._probing:
            raise ProviderFailure(
                "CIRCUIT_OPEN",
                retryable=True,
                usage=ProviderUsage(0, 0, 0),
                retry_after_seconds=max(1.0, remaining),
            )

    def _retry_after(self, response: httpx2.Response) -> float | None:
        value = response.headers.get("retry-after")
        if value is None:
            return None
        try:
            seconds = float(value)
        except ValueError:
            try:
                instant = parsedate_to_datetime(value)
                seconds = (instant - self.clock.now()).total_seconds()
            except (TypeError, ValueError, OverflowError):
                return None
        return max(0.0, seconds) if math.isfinite(seconds) and seconds <= 86_400 else None


@dataclass(frozen=True)
class InferenceTask:
    """Internal task input before a reservation exists; never accepts an owner from data."""

    role: ModelRole
    prompt_version: str
    prompt: str = field(repr=False)
    max_input_tokens: int
    max_output_tokens: int
    timeout_seconds: float

    def request(self, registry: ModelRegistry) -> LlmRequest:
        model = registry.resolve(self.role)
        return LlmRequest(
            self.role,
            model.model_id,
            registry.config.version,
            self.prompt_version,
            self.prompt,
            CallLimits(
                UUID(int=0), self.timeout_seconds, self.max_input_tokens, self.max_output_tokens
            ),
        )


class BudgetedInference:
    """Fresh worst-case reservations per attempt; never refund ambiguous charges.

    HTTP outages, 429 and truncation fail to the workflow's bounded retry policy.
    Only a syntactically/schema-invalid answer can trigger one charged repair.
    The original answer, validation details and hidden reasoning are never reused.
    """

    def __init__(self, llm: NebiusLLM, budget: Budget, *, run_id: UUID | None) -> None:
        self.llm, self.budget, self.run_id = llm, budget, run_id

    async def infer[T: DomainModel](
        self,
        task: InferenceTask,
        response_model: type[T],
        *,
        total_timeout_seconds: int,
        allow_repair: bool = True,
    ) -> LlmResponse[T]:
        if type(total_timeout_seconds) is not int or not 1 <= total_timeout_seconds <= 120:
            raise ValueError("Inference requires a bounded total deadline")
        request = task.request(self.llm.registry)
        try:
            async with asyncio.timeout(total_timeout_seconds):
                return await self._infer(
                    request, response_model, total_timeout_seconds, allow_repair
                )
        except TimeoutError:
            raise ProviderFailure("PROVIDER_TIMEOUT", retryable=True) from None

    async def _infer[T: DomainModel](
        self,
        request: LlmRequest,
        response_model: type[T],
        total_timeout_seconds: int,
        allow_repair: bool,
    ) -> LlmResponse[T]:
        deadline = self.llm.clock.monotonic() + total_timeout_seconds
        inputs = outputs = 0
        for attempt in range(2 if allow_repair else 1):
            remaining = min(request.limits.timeout_seconds, deadline - self.llm.clock.monotonic())
            timeout = math.floor(remaining)
            if timeout < 1:
                raise ProviderFailure("PROVIDER_TIMEOUT", retryable=True)
            bounded = replace(request, limits=replace(request.limits, timeout_seconds=timeout))
            model, payload = self.llm.prepare(bounded, response_model, repair=attempt == 1)
            quote = quote_model_call(
                self.llm.registry,
                request.role,
                input_token_limit=request.limits.max_input_tokens,
                output_token_limit=request.limits.max_output_tokens,
            )
            reservation = await self.budget.reserve(self.run_id, quote, timeout_seconds=timeout)
            bounded = replace(
                bounded, limits=replace(bounded.limits, reservation_id=reservation.id)
            )
            usage: ProviderUsage | None = None
            try:
                # reserve/reconcile transactions are closed before/after provider I/O.
                remaining = min(
                    reservation.expires_at.timestamp() - self.llm.clock.now().timestamp(),
                    deadline - self.llm.clock.monotonic(),
                    timeout,
                )
                if remaining <= 0:
                    raise ProviderFailure(
                        "PROVIDER_TIMEOUT", retryable=True, usage=ProviderUsage(0, 0, 0)
                    )
                bounded = replace(
                    bounded, limits=replace(bounded.limits, timeout_seconds=remaining)
                )
                try:
                    model, payload = self.llm.prepare(bounded, response_model, repair=attempt == 1)
                except DomainError:
                    usage = ProviderUsage(0, 0, 0)
                    raise
                result = await self.llm._generate(bounded, response_model, model, payload)
                usage = result.usage
            except ProviderFailure as failure:
                usage = failure.usage or usage
                if attempt == 0 and allow_repair and failure.code == "SCHEMA_INVALID":
                    if usage is not None:
                        inputs += usage.input_tokens
                        outputs += usage.output_tokens
                    continue
                raise
            finally:
                # Shield durable accounting when the worker is cancelled during a paid call.
                accounting = asyncio.create_task(self.budget.reconcile(reservation, usage))
                try:
                    await asyncio.shield(accounting)
                except asyncio.CancelledError:
                    await accounting
                    raise
            return LlmResponse(
                result.value,
                ProviderUsage(inputs + usage.input_tokens, outputs + usage.output_tokens, None),
            )
        raise ProviderFailure("SCHEMA_INVALID")


def bind_nebius(dependencies: Dependencies, llm: NebiusLLM) -> Dependencies:
    """Explicit real development binding; no registry/composition source edit or fake fallback."""
    provider: LLM = llm
    return replace(dependencies, llm=provider, provider_mode="real")
