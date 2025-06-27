from abc import ABC, abstractmethod

from src.schemas.payload import Payload


class Deserializer(ABC):
    @abstractmethod
    def deserialize(self, payload: bytes) -> Payload: ...
