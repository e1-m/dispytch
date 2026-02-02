import asyncio
import random
from inspect import isawaitable
from typing import Callable, Any, Sequence

from dispytch.listener.consumer import EventSubscription


class Handler:
    def __init__(
            self,
            func: Callable[..., Any],
            subscription: EventSubscription,
            retries: int = 0,
            retry_on: Sequence[type[Exception]] | None = None,
            base_delay_sec: float = 1.0,
            max_delay_sec: float = 30.0,
            jitter: Callable[[float], float] = lambda t: random.uniform(0, t),
    ):
        self.func = func
        self.subscription = subscription
        self.retries = abs(retries)
        self.base_delay = max(0.0, base_delay_sec)
        self.max_delay = max_delay_sec
        self.retry_on = tuple(retry_on) if retry_on is not None else None
        self.jitter = jitter

    async def handle(self, *args, **kwargs):
        for attempt in range(self.retries + 1):  # noqa
            try:
                res = self.func(*args, **kwargs)
                if isawaitable(res):
                    return await res
                return res
            except Exception as e:
                should_retry = (
                        self.retry_on is None or
                        isinstance(e, self.retry_on)
                )

                if attempt == self.retries or not should_retry:
                    raise e

                delay = min(
                    self.max_delay,
                    self.base_delay * (2 ** attempt)
                )

                jittered_delay = self.jitter(delay)

                await asyncio.sleep(jittered_delay)
