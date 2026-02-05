import logging

from dispytch.di.event import Event
from typing import Protocol


class DeadLetterHandler(Protocol):
    async def handle(self, error: Exception, **kwargs) -> None: ...


class DeadLetterLogger:
    @staticmethod
    async def handle(error: Exception, event: Event) -> None:
        logging.exception(f"Handling failed for event {event} with error: {error}")
