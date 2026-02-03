import logging
from abc import ABC, abstractmethod


class DeadLetterHandler(ABC):
    @abstractmethod
    async def handle(self, event: dict, error: Exception) -> None: ...


class DeadLetterLogger(DeadLetterHandler):
    async def handle(self, event: dict, error: Exception) -> None:
        logging.exception(f"Handling failed for event {event} with error: {error}")
