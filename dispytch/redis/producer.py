from pydantic import BaseModel
from redis.asyncio import Redis

from dispytch.emitter.producer import Producer
from dispytch.serialization.serializer import Serializer
from dispytch.serialization.json import JSONSerializer


class RedisProducer(Producer):
    def __init__(self,
                 redis: Redis,
                 serializer: Serializer = None,
                 ) -> None:
        self.redis = redis
        self.serializer = serializer or JSONSerializer()

    async def send(self, topic: str, payload: dict, config: BaseModel | None = None):
        await self.redis.publish(topic, self.serializer.serialize(payload))
