from typing import Protocol, Callable, Awaitable, Any

from dispytch.listener.handler import EventHandlerContext


class Middleware(Protocol):
    async def dispatch(self, ctx: EventHandlerContext, call_next: Callable[..., Awaitable[Any]]): ...
