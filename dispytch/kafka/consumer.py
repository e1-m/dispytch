from typing import AsyncIterator
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer, ConsumerRecord, TopicPartition

from dispytch.dispatcher.consumer import Consumer, Message, EventSubscription

logger = logging.getLogger(__name__)


class KafkaEventSubscription(EventSubscription):
    topic: str = "*"


class KafkaConsumer(Consumer):
    def __init__(self, consumer: AIOKafkaConsumer):
        self.consumer = consumer
        self._waiting_for_commit: dict[UUID, ConsumerRecord] = {}

    async def listen(self) -> AsyncIterator[Message]:
        async for message in self.consumer:
            msg = Message(subscription=KafkaEventSubscription(topic=message.topic),
                          payload=message.value)

            self._waiting_for_commit[msg.id] = message

            yield msg

    async def ack(self, message: Message):
        msg = self._waiting_for_commit.pop(message.id)
        tp = TopicPartition(msg.topic, msg.partition)
        return await self.consumer.commit({tp: msg.offset + 1})
