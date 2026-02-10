import uuid
from abc import ABC, abstractmethod
from typing import AsyncIterator

from pydantic import BaseModel, Field, ConfigDict


class EventSubscription(BaseModel, ABC):
    model_config = ConfigDict(frozen=True)

    @property
    def _values(self) -> tuple:
        return tuple(self.model_dump().values())

    def get_route_segments(self, delimiter: str = None) -> tuple[str, ...]:
        str_values = [str(v) for v in self._values]

        if delimiter is None:
            return tuple(str_values)

        return tuple(delimiter.join(str_values).split(delimiter))

    def __hash__(self) -> int:
        return hash(self._values)


class Message(BaseModel):
    """Represents a raw message received from a message broker."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    subscription: EventSubscription
    payload: bytes


class Consumer(ABC):
    @abstractmethod
    def listen(self) -> AsyncIterator[Message]: ...

    @abstractmethod
    async def ack(self, message: Message): ...
