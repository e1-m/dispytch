import asyncio
from typing import Protocol, Callable, Awaitable, Any

from dispytch.listener.dlh import DeadLetterHandler
from dispytch.listener.handler import EventHandlerContext
from dispytch.listener.retry_policy import RetryPolicy


class Middleware(Protocol):
    async def dispatch(self, ctx: EventHandlerContext, call_next: Callable[[EventHandlerContext], Awaitable[Any]]): ...


class RetryMiddleware:
    def __init__(self, retry_policy: RetryPolicy):
        self.retry_policy = retry_policy

    async def dispatch(self, ctx: EventHandlerContext, call_next: Callable[[EventHandlerContext], Awaitable[Any]]):
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


class DeadLetterMiddleware:
    def __init__(self, dlh: DeadLetterHandler):
        self.dlh = dlh

    async def dispatch(self, ctx: EventHandlerContext, call_next: Callable[[EventHandlerContext], Awaitable[Any]]):
        try:
            return await call_next(ctx)
        except Exception as err:
            await self.dlh.handle(ctx, err)
