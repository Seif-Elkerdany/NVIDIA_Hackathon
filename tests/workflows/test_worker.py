"""Deterministic retry and explicit-composition boundaries."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from tests.fakes.providers import FakeClock

from benefitbridge.composition import HandlerBinding
from benefitbridge.domain.base import DomainModel
from benefitbridge.ports import ActorContext, JobScope
from benefitbridge.workflows.queue import PostgresQueue
from benefitbridge.workflows.worker import RetryableStageError, Worker, retry_delay


@pytest.mark.parametrize("attempt,low,high", [(1, 1, 2), (2, 2, 4), (3, 4, 8)])
def test_exponential_jitter_is_bounded(attempt, low, high):
    assert retry_delay(attempt, 0) == low
    assert retry_delay(attempt, 1) == high
    assert retry_delay(attempt, 0.5, 45) == 45


@pytest.mark.parametrize(
    "attempt,jitter,after",
    [
        (0, 0, 0),
        (4, 0, 0),
        (1, -1, 0),
        (1, 2, 0),
        (1, float("nan"), 0),
        (1, 0, float("inf")),
        (1, 0, -1),
    ],
)
def test_invalid_retry_inputs_are_rejected(attempt, jitter, after):
    with pytest.raises(ValueError):
        retry_delay(attempt, jitter, after)


def test_retry_after_does_not_expose_provider_body():
    error = RetryableStageError("RATE_LIMITED", retry_after=20)
    assert error.retryable and error.retry_after == 20
    with pytest.raises(ValueError):
        RetryableStageError("RATE_LIMITED", retry_after=float("nan"))


def test_worker_rejects_missing_models_and_wrong_scope():
    class Handler:
        async def handle(self, context):
            pass

    queue = PostgresQueue(
        async_sessionmaker(), FakeClock(), {}, actor=ActorContext(uuid4(), 0, "synthetic")
    )
    with pytest.raises(ValueError, match="input model"):
        Worker(queue, {"stage": HandlerBinding(Handler())})
    with pytest.raises(ValueError, match="scoped handler"):
        Worker(queue, {"stage": HandlerBinding(Handler(), JobScope.PUBLIC)})


def test_worker_rejects_synchronous_handlers():
    class Handler:
        def handle(self, context):
            pass

    queue = PostgresQueue(
        async_sessionmaker(),
        FakeClock(),
        {"stage": DomainModel},
        actor=ActorContext(uuid4(), 0, "synthetic"),
    )
    with pytest.raises(ValueError, match="scoped handler"):
        Worker(queue, {"stage": HandlerBinding(Handler())})
