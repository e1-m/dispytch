import asyncio
import random
from inspect import isawaitable
from typing import Callable, Any, Sequence

from dispytch.di.builder import get_dependency_tree
from dispytch.di.context import DIContext
from dispytch.listener.consumer import EventSubscription
from dispytch.listener.dlq import DeadLetterHandler


class Handler:
    def __init__(
            self,
            func: Callable[..., Any],
            subscription: EventSubscription,
            dlh: DeadLetterHandler = None,
            retries: int = 0,
            retry_on: Sequence[type[Exception]] | None = None,
            base_delay_sec: float = 1.0,
            max_delay_sec: float = 30.0,
            jitter: Callable[[float], float] = lambda t: random.uniform(0, t),
    ):
        self.func = func
        self.dependency_tree = get_dependency_tree(func)
        self.subscription = subscription
        self.dlh = dlh

        self.retries = abs(retries)
        self.base_delay = max(0.0, base_delay_sec)
        self.max_delay = max_delay_sec
        self.retry_on = tuple(retry_on) if retry_on is not None else None
        self.jitter = jitter

    async def handle(self, ctx: DIContext):
        for attempt in range(self.retries + 1):  # noqa
            try:
                async with self.dependency_tree.resolve(
                    ctx
                ) as deps:
                    res = self.func(**deps)

                    if isawaitable(res):
                        return await res
                    return res
            except Exception as e:
                should_retry = (
                        self.retry_on is None or
                        isinstance(e, self.retry_on)
                )

                if attempt == self.retries or not should_retry:
                    if self.dlh is None:
                        raise e
                    return await self.dlh.handle(ctx.event, e)

                delay = min(
                    self.max_delay,
                    self.base_delay * (2 ** attempt)
                )

                jittered_delay = self.jitter(delay)

                await asyncio.sleep(jittered_delay)
