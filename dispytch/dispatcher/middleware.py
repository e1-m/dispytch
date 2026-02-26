from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import reduce
from typing import TypeAlias, Callable, Awaitable, Any


@dataclass
class EventHandlerContext:
    event: dict
    event_route: tuple[str, ...]


NextCall: TypeAlias = Callable[[EventHandlerContext], Awaitable[Any]]


class Middleware(ABC):
    @abstractmethod
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall): ...


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
