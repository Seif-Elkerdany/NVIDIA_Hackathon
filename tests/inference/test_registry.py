import json
from datetime import timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError
from tests.fakes.providers import FakeClock

from benefitbridge.config import ConfigurationError
from benefitbridge.domain.errors import DomainError
from benefitbridge.inference.registry import (
    ModelRegistry,
    ModelSpec,
    PreflightReport,
    ProbeEvidence,
    RegistryConfig,
)
from benefitbridge.ports import ModelRole


def model(role: ModelRole | str = ModelRole.REASON, **changes: object) -> ModelSpec:
    values: dict[str, object] = {
        "role": role,
        "model_id": f"synthetic-{str(role).lower()}",
        "endpoint": "https://inference.synthetic.invalid/v1/chat/completions",
        "context_tokens": 4096,
        "max_output_tokens": 128,
        "json_schema": True,
        "tools": False,
        "timeout_seconds": 5,
        "price_version": "synthetic-price-v1",
        "price_basis": "USD_PER_MILLION_TOKENS",
        "input_price": "0.013",
        "output_price": "0.047",
        "metadata_source": "https://metadata.synthetic.invalid/models",
        "verified_at": FakeClock().now(),
    }
    return ModelSpec.model_validate(values | changes)


def registry(*models: ModelSpec) -> ModelRegistry:
    return ModelRegistry(RegistryConfig(version="synthetic-registry-v1", models=models))


def report(current: ModelRegistry, **changes: object) -> PreflightReport:
    evidence = tuple(
        ProbeEvidence(
            role=spec.role,
            status="PASSED",
            checked_at=FakeClock().now(),
            schema_passed=True,
            tools_passed=spec.tools,
            calls=2 if spec.tools else 1,
            input_tokens=10,
            output_tokens=8,
            estimated_cost_microusd=spec.cost_microusd(10, 8),
            minimal_response='{"ok":true}',
        )
        for spec in current.config.models
    )
    values: dict[str, object] = {
        "configuration": current.config,
        "registry_version": current.config.version,
        "registry_fingerprint": current.fingerprint,
        "mode": "real",
        "results": evidence,
    }
    return PreflightReport.model_validate(values | changes)


def test_environment_requires_explicit_verified_metadata_and_no_names_or_prices() -> None:
    empty = ModelRegistry.from_environment({})
    assert empty.readiness(FakeClock()).reason == "MISSING_REASON"
    configured = registry(model(model_id="arbitrary/configured-id", input_price="12.345"))
    loaded = ModelRegistry.from_environment(
        {"MODEL_REGISTRY_JSON": configured.config.model_dump_json()}
    )
    assert loaded.resolve(ModelRole.REASON).model_id == "arbitrary/configured-id"
    assert loaded.resolve(ModelRole.REASON).input_price == Decimal("12.345")
    assert loaded.fingerprint == configured.fingerprint
    assert loaded.readiness(FakeClock()).reason == "PREFLIGHT_REQUIRED"


def test_missing_deep_is_allowed_and_fast_uses_single_reason_without_fake_fallback() -> None:
    current = registry(model())
    state = current.readiness(FakeClock(), report(current))
    assert state.inference_available
    assert not state.deep_available and not state.routing_comparison_available
    assert current.resolve(ModelRole.FAST) == current.resolve(ModelRole.REASON)
    with pytest.raises(DomainError, match="unavailable"):
        current.resolve(ModelRole.DEEP)


def test_missing_reason_never_becomes_ready_even_with_fast_deep() -> None:
    current = registry(model(ModelRole.FAST), model(ModelRole.DEEP))
    assert current.readiness(FakeClock(), report(current)).reason == "MISSING_REASON"


def test_fixture_metadata_never_proves_real_readiness() -> None:
    current = registry(model())
    assert not current.readiness(FakeClock(), report(current, mode="fixture")).inference_available


def test_preflight_expiration_and_future_times_fail_closed() -> None:
    current = registry(model())
    evidence = report(current)
    clock = FakeClock()
    clock.advance(current.config.preflight_ttl_seconds)
    assert current.readiness(clock, evidence).reason == "PREFLIGHT_STALE"
    future = evidence.results[0].model_copy(
        update={"checked_at": clock.now() + timedelta(seconds=1)}
    )
    updated = evidence.model_copy(update={"results": (future,)})
    assert current.readiness(clock, updated).reason == "PREFLIGHT_STALE"


@pytest.mark.parametrize(
    "change",
    [
        {"model_id": "changed"},
        {"input_price": "2"},
        {"price_version": "new-price"},
        {"context_tokens": 8192},
        {"tools": True},
        {"endpoint": "https://other.synthetic.invalid/v1/chat/completions"},
    ],
)
def test_any_metadata_change_invalidates_preflight(change: dict[str, object]) -> None:
    previous = registry(model())
    updated = registry(model(**change))
    assert updated.readiness(FakeClock(), report(previous)).reason == "REGISTRY_CHANGED"


def test_optional_deep_failure_does_not_block_reason_and_required_fast_failure_does() -> None:
    current = registry(model(), model(ModelRole.FAST), model(ModelRole.DEEP, tools=True))
    evidence = report(current)
    failed = ProbeEvidence(
        role=ModelRole.DEEP, status="FAILED", checked_at=FakeClock().now(), error_code="HTTP_ERROR"
    )
    evidence = evidence.model_copy(update={"results": evidence.results[:2] + (failed,)})
    state = current.readiness(FakeClock(), evidence)
    assert (
        state.inference_available
        and not state.deep_available
        and state.routing_comparison_available
    )
    evidence = evidence.model_copy(
        update={
            "results": (
                evidence.results[0],
                failed.model_copy(update={"role": ModelRole.FAST}),
                failed,
            )
        }
    )
    assert current.readiness(FakeClock(), evidence).reason == "PREFLIGHT_FAILED"


def test_fingerprint_is_order_independent_and_roles_share_metadata_consistently() -> None:
    reason, fast = model(), model(ModelRole.FAST)
    assert registry(reason, fast).fingerprint == registry(fast, reason).fingerprint
    with pytest.raises(ValidationError):
        registry(reason, reason)
    with pytest.raises(ValidationError):
        registry(reason, model(ModelRole.FAST, model_id=reason.model_id, input_price="5"))


@pytest.mark.parametrize(
    "change",
    [
        {"context_tokens": True},
        {"json_schema": "true"},
        {"input_price": 0.3},
        {"input_price": "NaN"},
        {"output_price": "-1"},
        {"max_output_tokens": 4096},
        {"timeout_seconds": 0},
        {"role": "UNKNOWN"},
        {"verified_at": "2026-10-01T00:00:00"},
        {"extra": 1},
        {"endpoint": "https://host.invalid/path?key=secret"},
        {"endpoint": "https://user:secret@host.invalid/path"},
        {"endpoint": "http://host.invalid"},
    ],
)
def test_invalid_metadata_is_rejected(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        model(**change)


def test_configuration_errors_are_safe_and_decimal_cost_rounds_up() -> None:
    with pytest.raises(ConfigurationError) as caught:
        ModelRegistry.from_json(json.dumps({"secret": "sensitive-value"}))
    assert "sensitive-value" not in str(caught.value)
    assert model().cost_microusd(10, 10) == 1
    with pytest.raises(ValueError):
        model().cost_microusd(True, 10)


def test_duplicate_json_keys_and_oversized_registry_are_rejected() -> None:
    for raw in ['{"version":"first","version":"second"}', " " * 65_537]:
        with pytest.raises(ConfigurationError):
            ModelRegistry.from_json(raw)
