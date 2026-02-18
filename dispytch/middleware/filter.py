from typing import Callable

from dispytch.dispatcher.handler import EventHandlerContext, NextCall, Middleware


class Filter(Middleware):
    def __init__(self, filter: Callable[[EventHandlerContext], bool]):
        self.filter = filter

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        if self.filter(ctx):
            return await call_next(ctx)
        return None
