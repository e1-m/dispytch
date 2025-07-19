from abc import ABC, abstractmethod

from pydantic import BaseModel


class MessagePayload(BaseModel):
    """Represents the deserialized content of a raw message received from a message broker."""
    id: str
    type: str
    body: dict
    timestamp: int


class Deserializer(ABC):
    @abstractmethod
    def deserialize(self, payload: bytes) -> MessagePayload: ...
