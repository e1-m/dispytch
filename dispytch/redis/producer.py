from pydantic import BaseModel
from redis.asyncio import Redis

from dispytch.emitter.producer import Producer, EventRoute


class RedisEventRoute(EventRoute):
    def __init__(self, channel: str):
        self.channel = channel

    def format_dynamic(self, **kwargs):
        try:
            return RedisEventRoute(channel=self.channel.format(**kwargs))
        except KeyError as e:
            raise RuntimeError(
                f"Missing an event field `{e.args[0]}` "
                f"used to form a channel name `{self.channel}`") from e
        except IndexError:
            raise RuntimeError(
                f"Malformed channel name `{self.channel}`. Use an event field name in {{}} "
            )


class RedisProducer(Producer):
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def send(self, payload: bytes, route: EventRoute, config: BaseModel | None = None):
        if not isinstance(route, RedisEventRoute):
            raise TypeError(
                f"Expected a RedisEventRoute when using RedisProducer got {type(route).__name__}"
            )

        await self.redis.publish(route.channel, payload)
