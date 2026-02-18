import asyncio
import random
from abc import ABC, abstractmethod
from typing import Sequence

from dispytch.dispatcher.handler import EventHandlerContext, NextCall, Middleware


class RetryPolicy(ABC):
    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool: ...

    @abstractmethod
    def get_delay(self, attempt: int, prev_delay: float) -> float: ...


class Retry(Middleware):
    def __init__(self, retry_policy: RetryPolicy):
        self.retry_policy = retry_policy

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        prev_delay = 0.0
        attempt = 0
        while True:
            try:
                return await call_next(ctx)
            except Exception as err:
                if not self.retry_policy.should_retry(attempt, err):
                    raise err

                prev_delay = self.retry_policy.get_delay(attempt, prev_delay)
                attempt += 1
                await asyncio.sleep(prev_delay)


class ExponentialBackoffWithFullJitter(RetryPolicy):
    def __init__(
            self,
            retries: int = 0,
            retry_on: Sequence[type[Exception]] | None = None,
            base_delay_sec: float = 1.0,
            max_delay_sec: float = 30.0,
    ):
        self.retries = abs(retries)
        self.retry_on = tuple(retry_on) if retry_on is not None else None
        self.base_delay = max(0.0, base_delay_sec)
        self.max_delay = max_delay_sec
        self.jitter = lambda t: random.uniform(0, t)

    def should_retry(self, attempt: int, error: Exception) -> bool:
        return attempt < self.retries and (self.retry_on is None or isinstance(error, self.retry_on))

    def get_delay(self, attempt: int, prev_delay: float) -> float:
        delay = min(
            self.max_delay,
            self.base_delay * (2 ** attempt)
        )
        return self.jitter(delay)
