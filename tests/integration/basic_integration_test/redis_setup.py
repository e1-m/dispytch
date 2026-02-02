import pytest_asyncio
from redis.asyncio import Redis

from dispytch import EventEmitter, EventListener
from dispytch.redis import RedisConsumer, RedisProducer, RedisEventRoute, RedisEventSubscription


@pytest_asyncio.fixture()
async def topics():
    return ['test_events']


@pytest_asyncio.fixture()
async def pubsub(topics):
    pubsub = Redis().pubsub()
    await pubsub.subscribe(*topics)
    yield pubsub


@pytest_asyncio.fixture()
async def redis():
    yield Redis()


@pytest_asyncio.fixture()
async def producer_redis(redis):
    return RedisProducer(redis)


@pytest_asyncio.fixture()
async def consumer_redis(pubsub):
    return RedisConsumer(pubsub)


@pytest_asyncio.fixture()
async def emitter_redis(producer_redis):
    return EventEmitter(
        producer=producer_redis
    )


@pytest_asyncio.fixture()
async def listener_redis(consumer_redis):
    return EventListener(
        consumer=consumer_redis,
    )


@pytest_asyncio.fixture()
async def subscription_redis(topics):
    return RedisEventSubscription(
        channel=topics[0]
    )


@pytest_asyncio.fixture()
async def event_route_redis(topics):
    return RedisEventRoute(
        channel=topics[0]
    )
