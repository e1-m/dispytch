from abc import ABC, abstractmethod

from pydantic import BaseModel


class Payload(BaseModel):
    id: str
    type: str
    body: dict


class Deserializer(ABC):
    @abstractmethod
    def deserialize(self, payload: bytes) -> Payload: ...
