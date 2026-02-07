import logging

from typing import Protocol

from dispytch.listener.handler import EventHandlerContext


class DeadLetterHandler(Protocol):
    async def handle(self, ctx: EventHandlerContext, error: Exception) -> None: ...


class DeadLetterLogger:
    @staticmethod
    async def handle(ctx: EventHandlerContext, error: Exception) -> None:
        logging.exception(f"Handling failed for event {ctx.event} with error: {error}")
