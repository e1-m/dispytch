from typing import Callable, Any, Awaitable

from dispytch.listener.handler import EventHandlerContext, NextCall


class ExceptionInterceptor:
    def __init__(self, handlers: dict[type[Exception], Callable[[EventHandlerContext, Exception], Awaitable[Any]]]):
        self._handlers = handlers

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        try:
            return await call_next(ctx)
        except Exception as err:
            for cls in type(err).mro():
                if issubclass(cls, Exception) and cls in self._handlers:
                    return await self._handlers[cls](ctx, err)

            raise err

    def add_handler(self, exception_type: type[Exception], handler: Callable[[EventHandlerContext, Exception], Awaitable[Any]]):
        self._handlers[exception_type] = handler
