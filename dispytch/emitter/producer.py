from abc import ABC, abstractmethod

from pydantic import BaseModel


class ProducerTimeout(Exception):
    pass


class Producer(ABC):
    @abstractmethod
    def send(self, topic: str, payload: dict, config: BaseModel | None = None): ...
