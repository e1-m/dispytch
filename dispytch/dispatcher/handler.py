from inspect import isawaitable
from typing import Callable, Any

from dispytch.di.context import DIContext
from dispytch.di.solver import DIResolver
from dispytch.dispatcher.middleware import MiddlewarePipeline, EventHandlerContext, Middleware


class Handler:
    def __init__(
            self,
            func: Callable[..., Any],
            subscription_pattern: tuple[str, ...],
            middlewares: list[Middleware] = None,
    ):
        self._user_func = func
        self._pipeline = MiddlewarePipeline(
            target_handler=self._invoke_with_injection,
            middlewares=middlewares
        )
        self.subscription_pattern = subscription_pattern

    async def handle(self, ctx: EventHandlerContext):
        return await self._pipeline.execute(ctx)

    async def _invoke_with_injection(self, ctx: EventHandlerContext):
        resolver = DIResolver(
            DIContext(
                event=ctx.event,
                actual_event_route=ctx.event_route,
                subscription_pattern=self.subscription_pattern,
            )
        )

        async with resolver.resolve(self._user_func) as dependencies:
            result = self._user_func(**dependencies)

            if isawaitable(result):
                return await result
            return result
