import time

from dispytch.dispatcher import EventHandlerContext, NextCall, Middleware
from .metrics import EVENTS_IN_PROGRESS, PROCESSING_LATENCY, EVENT_PROCESSED_TOTAL


class EventsInProgressMiddleware(Middleware):
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        EVENTS_IN_PROGRESS.inc()
        try:
            return await call_next(ctx)
        finally:
            EVENTS_IN_PROGRESS.dec()


class LatencyMiddleware(Middleware):
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        start_time = time.time()
        try:
            return await call_next(ctx)
        finally:
            latency = time.time() - start_time
            PROCESSING_LATENCY.observe(latency)


class TotalCounterMiddleware(Middleware):
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        try:
            return await call_next(ctx)
        finally:
            EVENT_PROCESSED_TOTAL.inc()
