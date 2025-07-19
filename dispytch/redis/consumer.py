import logging
from typing import AsyncIterator

from redis.asyncio.client import PubSub

from dispytch.listener.consumer import Consumer, Message

logger = logging.getLogger(__name__)


class RedisConsumer(Consumer):
    def __init__(self,
                 redis: PubSub):
        self.redis = redis

    async def listen(self) -> AsyncIterator[Message]:
        async for message in self.redis.listen():
            if message['type'] != 'message' and message['type'] != 'pmessage':
                continue

            yield Message(
                topic=message['channel'].decode('utf-8'),
                payload=message['data'],
            )

    async def ack(self, message: Message):
        ...
