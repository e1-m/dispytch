import logging
from typing import Protocol

from dispytch.listener.handler import EventHandlerContext, NextCall


class DeadLetterHandler(Protocol):
    async def handle(self, ctx: EventHandlerContext, error: Exception) -> None: ...


class DeadLetterMiddleware:
    def __init__(self, dlh: DeadLetterHandler):
        self.dlh = dlh

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        try:
            return await call_next(ctx)
        except Exception as err:
            await self.dlh.handle(ctx, err)


class DeadLetterLogger:
    @staticmethod
    async def handle(ctx: EventHandlerContext, error: Exception) -> None:
        logging.exception(f"Handling failed for event {ctx.event} with error: {error}")
