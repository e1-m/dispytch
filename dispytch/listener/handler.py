from dataclasses import dataclass
from functools import reduce
from inspect import isawaitable
from typing import Callable, Any

from dispytch.di.context import DIContext
from dispytch.di.solver import DIResolver
from dispytch.listener.middleware import Middleware, NextCall


@dataclass(frozen=True)
class EventHandlerContext:
    event: dict
    subscription_pattern: tuple[str, ...]
    actual_event_route: tuple[str, ...]


class MiddlewarePipeline:
    def __init__(
            self,
            target_handler: NextCall,
            middlewares: list[Middleware] | None = None
    ):
        self._target_handler = target_handler
        self._middlewares = middlewares if middlewares else []
        self._pipeline = self._compose_pipeline()

    def _compose_pipeline(self) -> NextCall:
        def apply_middleware(
                inner_handler: NextCall,
                middleware: Middleware
        ) -> NextCall:
            async def wrapped_layer(ctx: EventHandlerContext) -> Any:
                return await middleware.dispatch(ctx, inner_handler)

            return wrapped_layer

        return reduce(
            apply_middleware,
            reversed(self._middlewares),
            self._target_handler
        )

    async def execute(self, ctx: EventHandlerContext) -> Any:
        return await self._pipeline(ctx)


class Handler:
    def __init__(
            self,
            func: Callable[..., Any],
            middlewares: list[Middleware] = None,
    ):
        self._user_func = func
        self._pipeline = MiddlewarePipeline(
            target_handler=self._invoke_with_injection,
            middlewares=middlewares
        )

    async def handle(self, ctx: EventHandlerContext):
        return await self._pipeline.execute(ctx)

    async def _invoke_with_injection(self, ctx: EventHandlerContext):
        resolver = DIResolver(
            DIContext(
                event=ctx.event,
                subscription_pattern=ctx.subscription_pattern,
                actual_event_route=ctx.actual_event_route,
            )
        )

        async with resolver.resolve(self._user_func) as dependencies:
            result = self._user_func(**dependencies)

            if isawaitable(result):
                return await result
            return result
