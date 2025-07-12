from abc import ABC, abstractmethod


class Serializer(ABC):
    @abstractmethod
    def serialize(self, payload: dict) -> bytes: ...
