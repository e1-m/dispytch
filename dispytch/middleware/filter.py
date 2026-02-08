from typing import Callable

from dispytch.listener.handler import EventHandlerContext, NextCall


class FilterMiddleware:
    def __init__(self, filter: Callable[[EventHandlerContext], bool]):
        self.filter = filter

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        if self.filter(ctx):
            return await call_next(ctx)
        return None
