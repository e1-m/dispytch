import asyncio
from inspect import isawaitable
from typing import Callable, Any

from dispytch.di.solver import DIResolver
from dispytch.listener.dlq import DeadLetterHandler
from dispytch.listener.retry_policy import RetryPolicy


class Handler:
    def __init__(
            self,
            func: Callable[..., Any],
            dlh: DeadLetterHandler = None,
            retry_policy: RetryPolicy = None,
    ):
        self.func = func
        self.dlh = dlh
        self.retry_policy = retry_policy

    async def handle(self, di: DIResolver):
        prev_delay = 0.0
        attempt = 0

        while True:
            try:
                async with di.resolve(self.func) as deps:
                    res = self.func(**deps)

                    if isawaitable(res):
                        return await res
                    return res
            except Exception as err:
                if self.retry_policy is None or not self.retry_policy.should_retry(attempt, err):
                    if self.dlh is None:
                        raise err
                    return await self.dlh.handle(err)

                prev_delay = self.retry_policy.get_delay(attempt, prev_delay)
                attempt += 1
                await asyncio.sleep(prev_delay)
