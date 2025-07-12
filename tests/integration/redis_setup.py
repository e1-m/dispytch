import pytest_asyncio
from redis.asyncio import Redis

from dispytch import EventEmitter, EventListener
from dispytch.redis import RedisConsumer, RedisProducer


@pytest_asyncio.fixture()
async def topics():
    return ['test_events']


@pytest_asyncio.fixture()
async def pubsub(topics):
    pubsub = Redis().pubsub()
    await pubsub.subscribe(*topics)
    yield pubsub


@pytest_asyncio.fixture()
async def redis(bootstrap_servers):
    yield Redis()


@pytest_asyncio.fixture()
async def producer(redis):
    return RedisProducer(redis)


@pytest_asyncio.fixture()
async def consumer(pubsub):
    return RedisConsumer(pubsub)


@pytest_asyncio.fixture()
async def emitter_redis(producer):
    return EventEmitter(
        producer=producer
    )


@pytest_asyncio.fixture()
async def listener_redis(consumer):
    return EventListener(
        consumer=consumer,
    )
