from abc import ABC, abstractmethod
from typing import AsyncIterator

from pydantic import BaseModel


class Message(BaseModel):
    """Represents a raw message received from a message broker."""
    topic: str
    payload: bytes


class Consumer(ABC):
    @abstractmethod
    def listen(self) -> AsyncIterator[Message]: ...

    @abstractmethod
    def ack(self, message: Message): ...
