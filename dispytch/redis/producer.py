from pydantic import BaseModel
from redis.asyncio import Redis

from dispytch.emitter.producer import Producer
from dispytch.redis.event_route import RedisEventRoute


class RedisProducer(Producer):
    def __init__(self,
                 redis: Redis,
                 ) -> None:
        self.redis = redis

    async def send(self, payload: bytes, route: BaseModel, config: BaseModel | None = None):
        if not isinstance(route, RedisEventRoute):
            raise TypeError(
                f"Expected a RedisEventRoute when using RedisProducer got {type(route).__name__}"
            )

        await self.redis.publish(route.channel, payload)
