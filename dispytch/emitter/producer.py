from abc import ABC, abstractmethod

from pydantic import BaseModel


class ProducerTimeout(Exception):
    pass


class EventRoute(ABC):
    @abstractmethod
    def format_dynamic(self, **kwargs) -> "EventRoute": ...


class Producer(ABC):
    @abstractmethod
    async def send(self, payload: bytes, route: EventRoute, config: BaseModel | None = None): ...
