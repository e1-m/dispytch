from abc import ABC, abstractmethod


class Producer(ABC):
    @abstractmethod
    def send(self, topic: str, payload: dict): ...
