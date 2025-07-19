import uuid
from abc import ABC, abstractmethod
from typing import AsyncIterator

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a raw message received from a message broker."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    topic: str
    payload: bytes


class Consumer(ABC):
    @abstractmethod
    def listen(self) -> AsyncIterator[Message]: ...

    @abstractmethod
    def ack(self, message: Message): ...
