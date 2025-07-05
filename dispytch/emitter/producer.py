from abc import ABC, abstractmethod

from pydantic import BaseModel


class Producer(ABC):
    @abstractmethod
    def send(self, topic: str, payload: dict, config: BaseModel | None = None): ...
