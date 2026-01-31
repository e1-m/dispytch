import uuid
from abc import ABC, abstractmethod
from typing import AsyncIterator

from pydantic import BaseModel, Field


class EventSubscription(BaseModel, ABC):
    @abstractmethod
    def get_segments(self) -> tuple[str, ...]: ...


class Message(BaseModel):
    """Represents a raw message received from a message broker."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    subscription: EventSubscription
    payload: bytes


class Consumer(ABC):
    @abstractmethod
    def listen(self) -> AsyncIterator[Message]: ...

    @abstractmethod
    def ack(self, message: Message): ...
