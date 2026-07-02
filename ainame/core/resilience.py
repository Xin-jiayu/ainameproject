import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypeVar

import settings


T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    pass


async def with_timeout(awaitable: Awaitable[T], timeout: float | None = None) -> T:
    return await asyncio.wait_for(awaitable, timeout=timeout or settings.THIRD_PARTY_TIMEOUT_SECONDS)


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = settings.TASK_CIRCUIT_FAILURE_THRESHOLD
    reset_seconds: float = settings.TASK_CIRCUIT_RESET_SECONDS
    failure_count: int = 0
    opened_at: datetime | None = None

    @property
    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if datetime.now() - self.opened_at >= timedelta(seconds=self.reset_seconds):
            self.failure_count = 0
            self.opened_at = None
            return False
        return True

    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        if self.is_open:
            raise CircuitOpenError(f"{self.name} circuit is open")
        try:
            result = await func()
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = datetime.now()

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None


_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    breaker = _circuit_breakers.get(name)
    if breaker is None:
        breaker = CircuitBreaker(name=name)
        _circuit_breakers[name] = breaker
    return breaker
