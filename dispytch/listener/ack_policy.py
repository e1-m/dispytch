from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Awaitable, Any


class AckPolicy(ABC):
    @abstractmethod
    async def execute(
            self,
            ack_message: Callable[..., Awaitable[Any]],
            process_tasks: Callable[..., Awaitable[list[Any]]]
    ):
        pass


class AckAfterProcessing(AckPolicy):
    async def execute(
            self,
            ack_message: Callable[..., Awaitable[Any]],
            process_tasks: Callable[..., Awaitable[list[Any]]]
    ):
        _ = await process_tasks()
        await ack_message()


class AckBeforeProcessing(AckPolicy):
    async def execute(
            self,
            ack_message: Callable[..., Awaitable[Any]],
            process_tasks: Callable[..., Awaitable[list[Any]]]
    ):
        await ack_message()
        await process_tasks()
