from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.schemas.event import Event


class Consumer(ABC):
    @abstractmethod
    def listen(self) -> AsyncIterator[Event]: ...
