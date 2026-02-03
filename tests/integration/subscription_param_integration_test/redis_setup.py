import pytest_asyncio
from redis.asyncio import Redis

from dispytch import EventEmitter, EventListener
from dispytch.redis import RedisConsumer, RedisProducer, RedisEventRoute, RedisEventSubscription
from dispytch.serialization.msgpack import MessagePackDeserializer, MessagePackSerializer


@pytest_asyncio.fixture()
async def patterns():
    return ['test.events.*']


@pytest_asyncio.fixture()
async def pubsub(patterns):
    pubsub = Redis().pubsub()
    await pubsub.psubscribe(*patterns)
    yield pubsub


@pytest_asyncio.fixture()
async def redis():
    yield Redis()


@pytest_asyncio.fixture()
async def dispytch_redis_producer(redis):
    return RedisProducer(redis)


@pytest_asyncio.fixture()
async def dispytch_redis_consumer(pubsub):
    return RedisConsumer(pubsub)


@pytest_asyncio.fixture()
async def emitter_redis(dispytch_redis_producer):
    return EventEmitter(
        producer=dispytch_redis_producer,
        serializer=MessagePackSerializer()
    )


@pytest_asyncio.fixture()
async def listener_redis(dispytch_redis_consumer):
    return EventListener(
        consumer=dispytch_redis_consumer,
        deserializer=MessagePackDeserializer(),
        route_delimiter='.'
    )


@pytest_asyncio.fixture()
async def subscription_redis():
    return RedisEventSubscription(
        channel="test.events.{value}"
    )


@pytest_asyncio.fixture()
async def wildcard_subscription_redis():
    return RedisEventSubscription(
        channel="test.events.*"
    )


@pytest_asyncio.fixture()
async def event_route_redis():
    return RedisEventRoute(
        channel="test.events.{value}"
    )
