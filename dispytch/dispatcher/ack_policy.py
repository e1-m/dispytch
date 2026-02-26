import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Awaitable, Any

logger = logging.getLogger(__name__)


class AckPolicy(ABC):
    @abstractmethod
    async def execute(
            self,
            ack_message: Callable[..., Awaitable[Any]],
            process_tasks: Callable[..., Awaitable[list[Any]]]
    ) -> list[Any]:
        pass


class AckAfterProcessing(AckPolicy):
    async def execute(
            self,
            ack_message: Callable[..., Awaitable[Any]],
            process_tasks: Callable[..., Awaitable[list[Any]]]
    ) -> list[Any]:
        results = await process_tasks()

        try:
            await ack_message()
        except Exception as e:
            logger.warning(f"Failed to ack message, expect redelivery from the broker. Error: {e}")

        return results


class AckBeforeProcessing(AckPolicy):
    async def execute(
            self,
            ack_message: Callable[..., Awaitable[Any]],
            process_tasks: Callable[..., Awaitable[list[Any]]]
    ) -> list[Any]:
        try:
            await ack_message()
        except Exception as e:
            logger.warning(f"Failed to ack message, expect redelivery from the broker. Error: {e}")

        return await process_tasks()
