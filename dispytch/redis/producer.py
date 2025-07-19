from pydantic import BaseModel
from redis.asyncio import Redis

from dispytch.emitter.producer import Producer


class RedisProducer(Producer):
    def __init__(self,
                 redis: Redis,
                 ) -> None:
        self.redis = redis

    async def send(self, topic: str, payload: bytes, config: BaseModel | None = None):
        await self.redis.publish(topic, payload)
