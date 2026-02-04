import logging
from abc import ABC, abstractmethod


# TODO: add DI support
class DeadLetterHandler(ABC):
    @abstractmethod
    async def handle(self, error: Exception) -> None: ...


class DeadLetterLogger(DeadLetterHandler):
    async def handle(self, error: Exception) -> None:
        logging.exception(f"Handling failed for event with error: {error}")
