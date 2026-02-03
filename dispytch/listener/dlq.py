import logging
from abc import ABC, abstractmethod

from dispytch.di.event import Event


class DeadLetterHandler(ABC):
    @abstractmethod
    async def handle_dead_letter(self, event: Event, error: Exception) -> None: ...


class DeadLetterLogger(DeadLetterHandler):
    async def handle_dead_letter(self, event: Event, error: Exception) -> None:
        logging.exception(f"Handling failed for event {event} with error: {error}")
