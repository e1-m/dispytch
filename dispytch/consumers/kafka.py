from typing import AsyncIterator

from aiokafka import AIOKafkaConsumer, ConsumerRecord, TopicPartition

from dispytch.deserializers import JSONDeserializer
from dispytch.listener.consumer import Consumer, Event
from dispytch.consumers.deserializer import Deserializer


class KafkaConsumer(Consumer):
    def __init__(self, consumer: AIOKafkaConsumer, deserializer: Deserializer = None):
        self.consumer = consumer
        self.deserializer = deserializer or JSONDeserializer()
        self._waiting_for_commit: dict[str, ConsumerRecord] = {}

    async def start(self):
        return await self.consumer.start()

    async def stop(self):
        return await self.consumer.stop()

    async def listen(self) -> AsyncIterator[Event]:
        async for msg in self.consumer:
            deserialized_payload = self.deserializer.deserialize(msg.value)

            event = Event(topic=msg.topic,
                          type=deserialized_payload.type,
                          body=deserialized_payload.body)

            self._waiting_for_commit[event.id] = msg

            yield event

    async def ack(self, event: Event):
        msg = self._waiting_for_commit.pop(event.id)
        tp = TopicPartition(msg.topic, msg.partition)
        await self.consumer.commit({tp: msg.offset + 1})
