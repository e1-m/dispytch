import asyncio
import logging
from typing import AsyncIterator

from redis.asyncio.client import PubSub

from dispytch.listener.consumer import Consumer, Event
from dispytch.serialization.deserializer import Deserializer
from dispytch.serialization.json import JSONDeserializer

logger = logging.getLogger(__name__)


class RedisConsumer(Consumer):
    def __init__(self,
                 redis: PubSub,
                 deserializer: Deserializer = None):
        self.redis = redis
        self.deserializer = deserializer or JSONDeserializer()

    async def listen(self) -> AsyncIterator[Event]:
        async for message in self.redis.listen():
            if message['type'] != 'message' and message['type'] != 'pmessage':
                continue

            deserialized_payload = self.deserializer.deserialize(message['data'])
            yield Event(
                topic=message['channel'].decode('utf-8'),
                **deserialized_payload.model_dump()
            )

    async def ack(self, event: Event):
        ...
