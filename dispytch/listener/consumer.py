import uuid
from abc import ABC, abstractmethod
from typing import AsyncIterator

from pydantic import BaseModel, Field


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    type: str
    body: dict


class Consumer(ABC):
    @abstractmethod
    def listen(self) -> AsyncIterator[Event]: ...

    @abstractmethod
    def ack(self, event: Event): ...
