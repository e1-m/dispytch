import asyncio
from typing import AsyncIterator
import logging

from aiokafka import AIOKafkaConsumer, ConsumerRecord, TopicPartition
from aiokafka.errors import KafkaError

from dispytch.deserializers import JSONDeserializer
from dispytch.listener.consumer import Consumer, Event
from dispytch.consumers.deserializer import Deserializer

logger = logging.getLogger(__name__)


class KafkaConsumer(Consumer):
    def __init__(self, consumer: AIOKafkaConsumer, deserializer: Deserializer = None):
        self.consumer = consumer
        self.deserializer = deserializer or JSONDeserializer()
        self._waiting_for_commit: dict[str, ConsumerRecord] = {}

    async def listen(self) -> AsyncIterator[Event]:
        async for msg in self.consumer:
            deserialized_payload = self.deserializer.deserialize(msg.value)

            event = Event(id=deserialized_payload.id,
                          topic=msg.topic,
                          type=deserialized_payload.type,
                          body=deserialized_payload.body)

            self._waiting_for_commit[event.id] = msg

            yield event

    async def ack(self, event: Event):
        try:
            msg = self._waiting_for_commit.pop(event.id)
        except KeyError as e:
            logger.warning(f"Tried to ack a non-existent or already acked event {event.id}")
            raise e

        tp = TopicPartition(msg.topic, msg.partition)

        max_retries = 3
        backoff = 1

        for attempt in range(1, max_retries + 1):
            try:
                return await self.consumer.commit({tp: msg.offset + 1})
            except KafkaError as e:
                if not e.retriable:
                    raise e

                if attempt == max_retries:
                    logger.critical(f"Commit failed after {max_retries} attempts for event {event.id}")
                    raise e

                await asyncio.sleep(backoff * attempt)
        return None
