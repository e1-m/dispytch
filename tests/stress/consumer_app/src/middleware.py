from dispytch import Middleware, NextCall, EventHandlerContext
from .metrics import EVENTS_IN_PROGRESS


class EventsInProgressMiddleware(Middleware):
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        EVENTS_IN_PROGRESS.inc()
        try:
            return await call_next(ctx)
        finally:
            EVENTS_IN_PROGRESS.dec()
