from abc import ABC, abstractmethod

from dispytch.listener.consumer import MessagePayload


class Deserializer(ABC):
    @abstractmethod
    def deserialize(self, payload: bytes) -> MessagePayload: ...
