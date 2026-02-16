import asyncio
import logging
from typing import AsyncIterator
from uuid import UUID

from aio_pika.abc import AbstractIncomingMessage, AbstractQueue

from dispytch import EventSubscription
from dispytch.dispatcher.consumer import Consumer, Message

logger = logging.getLogger(__name__)


class RabbitMQEventSubscription(EventSubscription):
    exchange: str = "*"
    queue: str = "*"
    routing_key: str = "*"


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
                msg = Message(
                    subscription=RabbitMQEventSubscription(
                        exchange=message.exchange,
                        queue=queue.name,
                        routing_key=message.routing_key
                    ),
                    payload=message.body
                )

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
        message = self._waiting_for_ack.pop(message.id)
        await message.ack()
