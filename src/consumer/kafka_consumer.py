from typing import AsyncIterator

from aiokafka import AIOKafkaConsumer

from src.consumer import Consumer
from src.listener.models import Event
from src.deserializer.deserializer import Deserializer


class KafkaConsumer(Consumer):
    def __init__(self, consumer: AIOKafkaConsumer, deserializer: Deserializer):
        self.consumer = consumer
        self.deserializer = deserializer

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
