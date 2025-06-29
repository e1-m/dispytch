from abc import ABC, abstractmethod

from src.consumer.models import Payload


class Deserializer(ABC):
    @abstractmethod
    def deserialize(self, payload: bytes) -> Payload: ...
