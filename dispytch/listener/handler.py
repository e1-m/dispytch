import asyncio
from inspect import isawaitable
from typing import Callable, Any

from dispytch.di.builder import get_dependency_tree
from dispytch.di.context import DIContext
from dispytch.listener.consumer import EventSubscription
from dispytch.listener.dlq import DeadLetterHandler
from dispytch.listener.retry import RetryPolicy


class Handler:
    def __init__(
            self,
            func: Callable[..., Any],
            subscription: EventSubscription,
            dlh: DeadLetterHandler = None,
            retry_policy: RetryPolicy = None,
    ):
        self.func = func
        self.dependency_tree = get_dependency_tree(func)
        self.subscription = subscription
        self.dlh = dlh
        self.retry_policy = retry_policy

    async def handle(self, ctx: DIContext):
        prev_delay = 0.0

        for attempt in range(self.retries + 1):  # noqa
            try:
                async with self.dependency_tree.resolve(ctx) as deps:
                    res = self.func(**deps)

                    if isawaitable(res):
                        return await res
                    return res
            except Exception as err:
                if self.retry_policy is None or not self.retry_policy.should_retry(attempt, err):
                    if self.dlh is None:
                        raise err
                    return await self.dlh.handle(ctx.event, err)

                prev_delay = self.retry_policy.get_delay(attempt, prev_delay)
                await asyncio.sleep(prev_delay)
