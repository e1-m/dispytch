import asyncio
from dataclasses import dataclass
from functools import reduce
from inspect import isawaitable
from typing import Callable, Any, Awaitable, Iterable

from dispytch.di.context import DIContext
from dispytch.di.solver import DIResolver
from dispytch.listener.dlh import DeadLetterHandler
from dispytch.listener.middleware import Middleware
from dispytch.listener.retry_policy import RetryPolicy


@dataclass
class EventHandlerContext:
    event: dict
    subscription_pattern: tuple[str, ...]
    actual_event_route: tuple[str, ...]


class MiddlewareChain:
    def __init__(
            self,
            func: Callable[..., Awaitable[Any]],
            middlewares: Iterable[Any] | None = None
    ):
        self.func = func
        self.middlewares = list(middlewares) if middlewares else []
        self._chain = self._build_chain()

    def _build_chain(self) -> Callable[..., Awaitable[Any]]:
        return reduce(
            lambda next_step, mw: self._wrap_middleware(mw, next_step),
            reversed(self.middlewares),
            self.func
        )

    @staticmethod
    def _wrap_middleware(mw, next_step):
        async def layer(ctx):
            return await mw.dispatch(ctx, next_step)

        return layer

    async def __call__(self, ctx: EventHandlerContext) -> Any:
        return await self._chain(ctx)


class Handler:
    def __init__(
            self,
            func: Callable[..., Any],
            dlh: DeadLetterHandler = None,
            retry_policy: RetryPolicy = None,
            middlewares: list[Middleware] = None,
    ):
        self.func = func
        self.dlh = dlh
        self.retry_policy = retry_policy
        self.middlewares = middlewares

    async def handle(self, ctx: EventHandlerContext):
        di = DIResolver(
            DIContext(
                event=ctx.event,
                subscription_pattern=ctx.subscription_pattern,
                actual_event_route=ctx.actual_event_route,
            )
        )
        prev_delay = 0.0
        attempt = 0
        while True:
            try:
                async with di.resolve(self.func) as deps:
                    res = self.func(**deps)

                    return await res if isawaitable(res) else res
            except Exception as err:
                should_retry = self.retry_policy is not None and self.retry_policy.should_retry(attempt, err)

                if not should_retry:
                    if self.dlh is None:
                        raise err

                    async with di.resolve_internal_only(self.dlh.handle) as deps:
                        return await self.dlh.handle(err, **deps)

                prev_delay = self.retry_policy.get_delay(attempt, prev_delay)
                attempt += 1
                await asyncio.sleep(prev_delay)
