import asyncio
import logging
from typing import AsyncIterator

from aio_pika.abc import AbstractIncomingMessage, AbstractQueue

from dispytch.listener.consumer import Consumer, Event
from dispytch.serialization.deserializer import Deserializer
from dispytch.serialization.json import JSONDeserializer

logger = logging.getLogger(__name__)


class RabbitMQConsumer(Consumer):
    def __init__(self,
                 *queues: AbstractQueue,
                 deserializer: Deserializer = None):
        self.queues = queues
        self.deserializer = deserializer or JSONDeserializer()
        self._waiting_for_ack: dict[str, AbstractIncomingMessage] = {}
        self._consumed_events_queue = asyncio.Queue()
        self._consumer_tasks = []

    async def _consume_queue(self, queue: AbstractQueue):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                deserialized_payload = self.deserializer.deserialize(message.body)

                event = Event(id=deserialized_payload.id,
                              topic=queue.name,
                              type=deserialized_payload.type,
                              body=deserialized_payload.body)

                self._waiting_for_ack[event.id] = message
                await self._consumed_events_queue.put(event)

    async def listen(self) -> AsyncIterator[Event]:
        self._consumer_tasks = [
            asyncio.create_task(self._consume_queue(queue))
            for queue in self.queues
        ]

        try:
            while True:
                yield await self._consumed_events_queue.get()
        finally:
            for task in self._consumer_tasks:
                task.cancel()
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)

    async def ack(self, event: Event):
        try:
            message = self._waiting_for_ack.pop(event.id)
        except KeyError as e:
            logger.warning(f"Tried to ack a non-existent or already acked event {event.id}")
            raise e

        try:
            await message.ack()
        except Exception as e:
            logger.error(f"Failed to ack message: {e}")
            raise e
