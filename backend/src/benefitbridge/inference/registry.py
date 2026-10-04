"""Versioned model metadata and offline readiness for R14.02.

Load with ``ModelRegistry.from_environment(mapping)`` using MODEL_REGISTRY_JSON,
or ``from_json`` for an operator registry file. No IDs, prices or capabilities
are inferred from model-family names. Readiness consumes persisted real
preflight evidence; constructing the registry never contacts a provider.
"""

import json
from collections.abc import Mapping
from decimal import ROUND_CEILING, localcontext
from hashlib import sha256
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import (
    Field,
    JsonValue,
    StrictBool,
    StrictInt,
    StrictStr,
    ValidationError,
    field_validator,
    model_validator,
)

from benefitbridge.config import ConfigurationError
from benefitbridge.domain.base import DecimalText, DomainModel, UtcTimestamp
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import Clock, ModelRole

MAX_REGISTRY_BYTES = 65_536
Name = Annotated[StrictStr, Field(min_length=1, max_length=256, pattern=r"^\S(?:.*\S)?$")]
PositiveInt = Annotated[StrictInt, Field(gt=0, le=2_147_483_647)]
NonnegativeInt = Annotated[StrictInt, Field(ge=0)]
ReadinessReason = Literal[
    "READY",
    "MISSING_REASON",
    "PREFLIGHT_REQUIRED",
    "PREFLIGHT_FAILED",
    "PREFLIGHT_STALE",
    "REGISTRY_CHANGED",
]
Price = Annotated[DecimalText, Field(max_digits=18, decimal_places=9)]
ProbeError = Literal[
    "HTTP_ERROR",
    "TIMEOUT",
    "INVALID_RESPONSE",
    "UNSUPPORTED",
    "BUDGET_EXCEEDED",
    "TOKEN_LIMIT_EXCEEDED",
]


class ModelSpec(DomainModel):
    role: ModelRole
    model_id: Name
    endpoint: Annotated[StrictStr, Field(max_length=2048)]
    provider: Literal["NEBIUS"] = "NEBIUS"
    context_tokens: PositiveInt
    max_output_tokens: PositiveInt
    json_schema: StrictBool
    tools: StrictBool
    timeout_seconds: Annotated[StrictInt, Field(ge=1, le=120)]
    price_version: Name
    price_basis: Literal["USD_PER_MILLION_TOKENS"]
    input_price: Price
    output_price: Price
    metadata_source: Annotated[StrictStr, Field(min_length=1, max_length=2048)]
    verified_at: UtcTimestamp

    @field_validator("endpoint", "metadata_source")
    @classmethod
    def safe_url(cls, value: str) -> str:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or any(char.isspace() for char in value)
        ):
            raise ValueError("Registry URLs require HTTPS without secrets or query strings")
        return value

    @model_validator(mode="after")
    def limits(self) -> Self:
        if self.max_output_tokens >= self.context_tokens:
            raise ValueError("Output limit must leave space for input tokens")
        return self

    def cost_microusd(self, input_tokens: int, output_tokens: int) -> int:
        """Ceiling price-based estimate; never presented as provider-billed cost."""
        if (
            type(input_tokens) is not int
            or type(output_tokens) is not int
            or min(input_tokens, output_tokens) < 0
        ):
            raise ValueError("Token counts must be nonnegative integers")
        with localcontext() as context:
            context.prec = 64
            return int(
                (
                    self.input_price * input_tokens + self.output_price * output_tokens
                ).to_integral_value(rounding=ROUND_CEILING)
            )


class RegistryConfig(DomainModel):
    version: Name
    models: Annotated[tuple[ModelSpec, ...], Field(max_length=3)] = ()
    preflight_ttl_seconds: Annotated[StrictInt, Field(ge=1, le=86_400)] = 3600

    @model_validator(mode="after")
    def unique_roles(self) -> Self:
        if len({model.role for model in self.models}) != len(self.models):
            raise ValueError("Each role may have only one configured model")
        # The same endpoint/model cannot have contradictory metadata by role.
        seen: dict[tuple[str, str], str] = {}
        for model in self.models:
            key = (model.endpoint, model.model_id)
            metadata = model.model_dump_json(exclude={"role"})
            if key in seen and seen[key] != metadata:
                raise ValueError("Shared models require consistent verified metadata")
            seen[key] = metadata
        return self


class ProbeEvidence(DomainModel):
    role: ModelRole
    status: Literal["PASSED", "FAILED", "NOT_RUN"]
    checked_at: UtcTimestamp
    schema_passed: StrictBool = False
    tools_passed: StrictBool = False
    calls: NonnegativeInt = 0
    input_tokens: NonnegativeInt | None = None
    output_tokens: NonnegativeInt | None = None
    estimated_cost_microusd: NonnegativeInt | None = None
    billed_microusd: NonnegativeInt | None = None
    elapsed_ms: NonnegativeInt = 0
    minimal_response: Literal['{"ok":true}'] | None = None
    error_code: ProbeError | None = None

    @model_validator(mode="after")
    def successful_evidence(self) -> Self:
        if self.status == "PASSED" and (
            not self.schema_passed
            or self.calls < 1
            or self.minimal_response is None
            or self.error_code is not None
            or self.input_tokens is None
            or self.output_tokens is None
            or self.estimated_cost_microusd is None
        ):
            raise ValueError("Passing preflight requires measured schema/usage evidence")
        if self.status == "FAILED" and self.error_code is None:
            raise ValueError("Failed preflight requires a safe error code")
        return self


class PreflightReport(DomainModel):
    configuration: RegistryConfig
    registry_version: Name
    registry_fingerprint: Annotated[StrictStr, Field(pattern=r"^[a-f0-9]{64}$")]
    mode: Literal["real", "fixture"]
    results: Annotated[tuple[ProbeEvidence, ...], Field(max_length=3)]

    @model_validator(mode="after")
    def unique_results(self) -> Self:
        if len({item.role for item in self.results}) != len(self.results):
            raise ValueError("Preflight roles must be unique")
        if (
            self.registry_version != self.configuration.version
            or self.registry_fingerprint != _fingerprint(self.configuration)
        ):
            raise ValueError("Preflight metadata does not match its fingerprint")
        if {item.role for item in self.results} != {
            item.role for item in self.configuration.models
        }:
            raise ValueError("Preflight must report every configured role")
        return self


class Readiness(DomainModel):
    inference_available: bool
    deep_available: bool
    routing_comparison_available: bool
    reason: ReadinessReason


def _fingerprint(config: RegistryConfig) -> str:
    data = config.model_dump(mode="json")
    data["models"] = sorted(data["models"], key=lambda item: item["role"])
    return sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ModelRegistry:
    def __init__(self, config: RegistryConfig) -> None:
        self.config = config

    @classmethod
    def from_json(cls, raw: str) -> Self:
        try:
            if len(raw.encode("utf-8")) > MAX_REGISTRY_BYTES:
                raise ValueError("Oversized registry")

            def unique_object(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
                result: dict[str, JsonValue] = {}
                for name, value in pairs:
                    if name in result:
                        raise ValueError("Duplicate registry keys")
                    result[name] = value
                return result

            config = RegistryConfig.model_validate(json.loads(raw, object_pairs_hook=unique_object))
        except (ValidationError, ValueError, RecursionError):
            raise ConfigurationError("Invalid model registry configuration") from None
        return cls(config)

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> Self:
        raw = environment.get("MODEL_REGISTRY_JSON")
        return (
            cls.from_json(raw) if raw is not None else cls(RegistryConfig(version="unconfigured"))
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.config)

    def configured(self, role: ModelRole) -> ModelSpec | None:
        return next((model for model in self.config.models if model.role == role), None)

    def resolve(self, role: ModelRole) -> ModelSpec:
        model = self.configured(role)
        if model is None and role == ModelRole.FAST:
            model = self.configured(ModelRole.REASON)
        if model is None:
            raise DomainError(
                "DEPENDENCY_UNAVAILABLE", "The requested model role is unavailable.", 503, False
            )
        return model

    def readiness(self, clock: Clock, report: PreflightReport | None = None) -> Readiness:
        def result(reason: ReadinessReason, deep: bool = False) -> Readiness:
            return Readiness(
                inference_available=reason == "READY",
                deep_available=deep,
                routing_comparison_available=reason == "READY" and distinct,
                reason=reason,
            )

        reason_model = self.configured(ModelRole.REASON)
        fast = self.configured(ModelRole.FAST)
        distinct = bool(
            reason_model
            and fast
            and (reason_model.endpoint, reason_model.model_id) != (fast.endpoint, fast.model_id)
        )
        if reason_model is None:
            return result("MISSING_REASON")
        if report is None or report.mode != "real":
            return result("PREFLIGHT_REQUIRED")
        if (
            report.registry_version != self.config.version
            or report.registry_fingerprint != self.fingerprint
        ):
            return result("REGISTRY_CHANGED")
        now = clock.now()
        evidence = {item.role: item for item in report.results}

        def status(
            model: ModelSpec,
        ) -> Literal["READY", "PREFLIGHT_REQUIRED", "PREFLIGHT_FAILED", "PREFLIGHT_STALE"]:
            item = evidence.get(model.role)
            if item is None or item.status == "NOT_RUN":
                return "PREFLIGHT_REQUIRED"
            if (
                item.status != "PASSED"
                or not model.json_schema
                or (model.tools and not item.tools_passed)
            ):
                return "PREFLIGHT_FAILED"
            age = (now - item.checked_at).total_seconds()
            if (
                age < 0
                or age >= self.config.preflight_ttl_seconds
                or model.verified_at > item.checked_at
            ):
                return "PREFLIGHT_STALE"
            return "READY"

        for model in (reason_model, fast):
            if model is not None and (state := status(model)) != "READY":
                return result(state)
        deep_model = self.configured(ModelRole.DEEP)
        return result("READY", deep_model is not None and status(deep_model) == "READY")
