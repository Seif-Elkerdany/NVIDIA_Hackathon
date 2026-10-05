"""Synthetic registry quotation; no provider calls or fabricated billing."""

import pytest
from pydantic import ValidationError
from tests.inference.test_registry import model, registry

from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import ModelRole
from benefitbridge.usage.budget import BudgetLimits, quote_model_call


def limits(**changes):
    return BudgetLimits.model_validate(
        {
            "run_microusd": 500000,
            "owner_daily_microusd": 2000000,
            "global_daily_microusd": 10000000,
            "run_concurrency": 1,
            "owner_concurrency": 2,
            "global_concurrency": 2,
            **changes,
        }
    )


def test_quote_reserves_configured_maximum_output_and_ceilings_decimal_prices():
    current = registry(model())
    quote = quote_model_call(current, ModelRole.REASON, input_token_limit=101)
    assert quote.output_token_limit == 128
    assert quote.maximum_microusd == 8
    assert quote.registry_version == current.config.version
    assert quote.registry_fingerprint == current.fingerprint
    assert quote.model.price_version == "synthetic-price-v1"


def test_explicit_output_bound_uses_the_same_verified_prices():
    quote = quote_model_call(
        registry(model()), ModelRole.REASON, input_token_limit=1, output_token_limit=1
    )
    assert quote.maximum_microusd == 1


def test_fast_fallback_preserves_the_resolved_reason_model():
    current = registry(model())
    quote = quote_model_call(current, ModelRole.FAST, input_token_limit=10)
    assert quote.model.role == ModelRole.REASON
    assert quote.model == current.resolve(ModelRole.FAST)
    with pytest.raises(DomainError):
        quote_model_call(current, ModelRole.DEEP, input_token_limit=10)


@pytest.mark.parametrize(
    "inputs,outputs",
    [(-1, 1), (True, 1), (1.5, 1), (1, False), (1, -1), (1, 129), (4096, 1), (2**31, 0)],
)
def test_invalid_token_bounds_never_produce_a_quote(inputs, outputs):
    with pytest.raises(ValidationError):
        quote_model_call(
            registry(model()),
            ModelRole.REASON,
            input_token_limit=inputs,
            output_token_limit=outputs,
        )


def test_quote_does_not_change_when_registry_is_replaced():
    current = registry(model())
    quote = quote_model_call(current, ModelRole.REASON, input_token_limit=100)
    current.config = registry(model(input_price="10.00")).config
    assert quote.maximum_microusd == 8
    with pytest.raises(ValidationError):
        quote.input_token_limit = 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_microusd", -1),
        ("owner_daily_microusd", True),
        ("global_daily_microusd", 1.5),
        ("global_daily_microusd", 2**63),
        ("run_concurrency", 0),
        ("owner_concurrency", -1),
        ("global_concurrency", True),
    ],
)
def test_limits_reject_invalid_money_and_concurrency(field, value):
    with pytest.raises(ValidationError):
        limits(**{field: value})


def test_funded_global_cap_is_required_and_zero_can_disable_spending():
    with pytest.raises(ValidationError):
        BudgetLimits(
            run_microusd=0,
            owner_daily_microusd=0,
            run_concurrency=1,
            owner_concurrency=2,
            global_concurrency=2,
        )
    assert limits(global_daily_microusd=0).global_daily_microusd == 0
