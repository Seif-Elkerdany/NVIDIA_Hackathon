"""Bounded handler execution with periodic lease renewal and crash-safe checkpoints."""

import asyncio
import inspect
import math
import random
from collections.abc import Callable, Mapping
from types import MappingProxyType
from uuid import UUID, uuid4

from benefitbridge.composition import HandlerBinding
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import StageHandler
from benefitbridge.workflows.queue import HEARTBEAT_SECONDS, Claim, PostgresQueue


class RetryableStageError(DomainError):
    """Adapters may expose a parsed, finite Retry-After without exposing provider bodies."""

    def __init__(self, code: str, *, retry_after: float = 0) -> None:
        if not math.isfinite(retry_after) or retry_after < 0:
            raise ValueError("Retry-After must be finite and nonnegative")
        super().__init__(code, "Stage dependency is unavailable", 503, retryable=True)
        self.retry_after = retry_after


def retry_delay(attempt: int, jitter: float, retry_after: float = 0) -> float:
    if (
        not 1 <= attempt <= 3
        or not 0 <= jitter <= 1
        or not math.isfinite(retry_after)
        or retry_after < 0
    ):
        raise ValueError("Invalid retry inputs")
    # Retry-After may exceed the jitter cap; it is never shortened. Queue.fail
    # refuses another attempt when that delay exceeds the remaining deadline.
    return float(max(retry_after, min(30, 2**attempt) * (0.5 + jitter / 2)))


class Worker:
    """Compose with Dependencies.handlers and an explicitly authorized queue partition.

    No provider is invented or selected here. Process termination leaves the
    durable lease for replacement; task cancellation also never deletes work.
    """

    def __init__(
        self,
        queue: PostgresQueue,
        handlers: Mapping[str, HandlerBinding],
        *,
        worker_id: UUID | None = None,
        jitter: Callable[[], float] = random.random,
        heartbeat_seconds: float = HEARTBEAT_SECONDS,
    ) -> None:
        if not 0 < heartbeat_seconds <= HEARTBEAT_SECONDS:
            raise ValueError("Heartbeat interval must be positive and at most 15 seconds")
        selected = {
            name: binding.handler
            for name, binding in handlers.items()
            if binding.scope == queue.scope
        }
        if not selected or any(
            not isinstance(handler, StageHandler) or not inspect.iscoroutinefunction(handler.handle)
            for handler in selected.values()
        ):
            raise ValueError("A worker requires an explicit scoped handler allowlist")
        if queue.actor is not None and set(selected) != set(queue.input_models):
            raise ValueError("Every private handler requires an explicit input model")
        self.queue = queue
        self.handlers = MappingProxyType(selected)
        self.worker_id = worker_id or uuid4()
        self.jitter = jitter
        self.heartbeat_seconds = heartbeat_seconds

    async def serve(self, stop: asyncio.Event, *, poll_seconds: float = 1) -> None:
        """Run until an operator stop; finish the current bounded stage first."""
        if not math.isfinite(poll_seconds) or poll_seconds <= 0:
            raise ValueError("Poll interval must be finite and positive")
        while not stop.is_set():
            if not await self.run_once():
                try:
                    await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
                except TimeoutError:
                    continue

    async def run_once(self) -> bool:
        await self.queue.dispatch()
        claim = await self.queue.claim(self.worker_id, tuple(self.handlers))
        if claim is None:
            return False
        await self.execute(claim)
        return True

    async def execute(self, claim: Claim) -> None:
        context = claim.context
        if claim.checkpoint is not None:
            await self.queue.publish(context, claim.checkpoint)
            return
        if not await self.queue.heartbeat(claim):
            await self.queue.fail(claim, "CANCELLED")
            return
        remaining = (context.deadline_at - self.queue.clock.now()).total_seconds()
        try:
            async with asyncio.timeout(remaining):
                async with asyncio.TaskGroup() as group:
                    task = group.create_task(self.handlers[context.stage].handle(context))
                    heartbeat = group.create_task(self._renew(claim))
                    try:
                        result = await task
                    finally:
                        heartbeat.cancel()
        except TimeoutError:
            await self.queue.fail(claim, "DEADLINE_EXCEEDED")
            return
        except BaseExceptionGroup as failures:
            # TaskGroup preserves cancellation and unexpected exceptions. Only
            # typed operational failures become a retry/failure receipt.
            operational, unexpected = failures.split(DomainError)
            if unexpected is not None:
                raise unexpected from failures
            assert operational is not None
            error = operational.exceptions[0]
            if not isinstance(error, DomainError):
                raise operational from failures
            await self._failure(claim, error)
            return
        except DomainError as error:
            await self._failure(claim, error)
            return
        try:
            if await self.queue.checkpoint(claim, result):
                await self.queue.publish(context, result)
            else:
                await self.queue.fail(claim, "CANCELLED")
        except DomainError as error:
            await self._failure(claim, error)

    async def _renew(self, claim: Claim) -> None:
        while True:
            await asyncio.sleep(self.heartbeat_seconds)
            if not await self.queue.heartbeat(claim):
                raise DomainError("LEASE_LOST", "Stage lease is unavailable", 409)

    async def _failure(self, claim: Claim, error: DomainError) -> None:
        delay = (
            retry_delay(
                claim.attempt,
                self.jitter(),
                error.retry_after if isinstance(error, RetryableStageError) else 0,
            )
            if error.retryable
            else None
        )
        await self.queue.fail(claim, error.code, delay)
