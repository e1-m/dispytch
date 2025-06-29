from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.listener.models import Event


class Consumer(ABC):
    @abstractmethod
    def listen(self) -> AsyncIterator[Event]: ...
