from dispytch import Middleware, EventHandlerContext, NextCall


class FilterEventType(Middleware):
    def __init__(self, event_type: str):
        self.event_type = event_type

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        if ctx.event['type'] == self.event_type:
            return await call_next(ctx)
        return None
