from typing import AsyncIterator

from aiokafka import AIOKafkaConsumer

from dispytch.deserializers import JSONDeserializer
from dispytch.listener.consumer import Consumer, Event
from dispytch.consumers.deserializer import Deserializer


class KafkaConsumer(Consumer):
    def __init__(self, consumer: AIOKafkaConsumer, deserializer: Deserializer = None):
        self.consumer = consumer
        self.deserializer = deserializer or JSONDeserializer()

    async def listen(self) -> AsyncIterator[Event]:
        await self.consumer.start()
        try:
            async for msg in self.consumer:
                deserialized_payload = self.deserializer.deserialize(msg.value)

                yield Event(topic=msg.topic,
                            type=deserialized_payload.type,
                            body=deserialized_payload.body)
        finally:
            await self.consumer.stop()
