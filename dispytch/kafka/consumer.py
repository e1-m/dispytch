import asyncio
from typing import AsyncIterator
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer, ConsumerRecord, TopicPartition
from aiokafka.errors import KafkaError

from dispytch.listener.consumer import Consumer, Message

logger = logging.getLogger(__name__)


class KafkaConsumer(Consumer):
    def __init__(self, consumer: AIOKafkaConsumer):
        self.consumer = consumer
        self._waiting_for_commit: dict[UUID, ConsumerRecord] = {}

    async def listen(self) -> AsyncIterator[Message]:
        async for message in self.consumer:
            msg = Message(topic=message.topic,
                          payload=message.value)

            self._waiting_for_commit[msg.id] = message

            yield msg

    async def ack(self, message: Message):
        try:
            msg = self._waiting_for_commit.pop(message.id)
        except KeyError as e:
            logger.warning(f"Tried to ack a non-existent or already acked message")
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
                    logger.critical(f"Commit failed after {max_retries} attempts for a message")
                    raise e

                await asyncio.sleep(backoff * attempt)
        return None
