import asyncio
import logging
from typing import AsyncIterator
from uuid import UUID

from aio_pika.abc import AbstractIncomingMessage, AbstractQueue

from dispytch.listener.consumer import Consumer, Message

logger = logging.getLogger(__name__)


class RabbitMQConsumer(Consumer):
    def __init__(self,
                 *queues: AbstractQueue):
        self.queues = queues
        self._waiting_for_ack: dict[UUID, AbstractIncomingMessage] = {}
        self._consumed_messages_queue = asyncio.Queue()
        self._consumer_tasks = []

    async def _consume_queue(self, queue: AbstractQueue):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                msg = Message(topic=message.routing_key,
                              payload=message.body)

                self._waiting_for_ack[msg.id] = message
                await self._consumed_messages_queue.put(msg)

    async def listen(self) -> AsyncIterator[Message]:
        self._consumer_tasks = [
            asyncio.create_task(self._consume_queue(queue))
            for queue in self.queues
        ]

        try:
            while True:
                yield await self._consumed_messages_queue.get()
        finally:
            for task in self._consumer_tasks:
                task.cancel()
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)

    async def ack(self, message: Message):
        try:
            message = self._waiting_for_ack.pop(message.id)
        except KeyError as e:
            logger.warning(f"Tried to ack a non-existent or already acked message")
            raise e

        try:
            await message.ack()
        except Exception as e:
            logger.error(f"Failed to ack message: {e}")
            raise e
