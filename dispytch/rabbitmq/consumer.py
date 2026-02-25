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
        self._is_running = False

    async def _consume_queue(self, queue: AbstractQueue):
        try:
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
                    self._consumed_messages_queue.put_nowait(msg)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Consumer task for queue %s failed: %s", queue.name, e)

    async def start(self):
        if self._is_running:
            logger.warning("Attempting to start an already running consumer.")
            return

        self._is_running = True
        self._consumer_tasks = [
            asyncio.create_task(self._consume_queue(queue))
            for queue in self.queues
        ]

    async def stop(self):
        if not self._is_running:
            logger.warning("Attempting to stop a non-running consumer.")
            return

        self._is_running = False

        for task in self._consumer_tasks:
            task.cancel()

        if self._consumer_tasks:
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)
            self._consumer_tasks.clear()

        await self._consumed_messages_queue.put(None)

    async def listen(self) -> AsyncIterator[Message]:
        while self._is_running:
            msg = await self._consumed_messages_queue.get()

            if msg is None:
                break

            yield msg

    async def ack(self, message: Message):
        await self._waiting_for_ack.pop(message.id).ack()
