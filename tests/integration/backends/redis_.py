import pytest_asyncio
from redis.asyncio import Redis

from dispytch import EventEmitter, EventDispatcher
from dispytch.redis import RedisConsumer, RedisProducer, RedisEventRoute, RedisEventSubscription
from dispytch.serialization.msgpack import MessagePackSerializer, MessagePackDeserializer

from tests.integration.support.types import Backend


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
    r = Redis()
    yield r


@pytest_asyncio.fixture()
async def producer_redis(redis):
    return RedisProducer(redis)


@pytest_asyncio.fixture()
async def consumer_redis(pubsub):
    return RedisConsumer(pubsub)


@pytest_asyncio.fixture()
async def backend_redis(producer_redis, consumer_redis, topics):
    emitter = EventEmitter(producer=producer_redis)
    listener = EventDispatcher(consumer=consumer_redis, route_delimiter='.')
    subscription = RedisEventSubscription(channel=topics[0])
    route = RedisEventRoute(channel=topics[0])

    return Backend(
        name="redis",
        emitter=emitter,
        listener=listener,
        subscription=subscription,
        route=route
    )


# --- Dynamic topics (subscription params) backend ---
@pytest_asyncio.fixture()
async def patterns():
    return ['test.events.*']


@pytest_asyncio.fixture()
async def pubsub_params(patterns):
    pubsub = Redis().pubsub()
    await pubsub.psubscribe(*patterns)
    yield pubsub


@pytest_asyncio.fixture()
async def redis_params():
    r = Redis()
    yield r


@pytest_asyncio.fixture()
async def producer_redis_params(redis_params):
    return RedisProducer(redis_params)


@pytest_asyncio.fixture()
async def consumer_redis_params(pubsub_params):
    return RedisConsumer(pubsub_params)


@pytest_asyncio.fixture()
async def backend_redis_params(producer_redis_params, consumer_redis_params):
    emitter = EventEmitter(producer=producer_redis_params, serializer=MessagePackSerializer())
    listener = EventDispatcher(consumer=consumer_redis_params, deserializer=MessagePackDeserializer(),
                               route_delimiter='.')
    subscription = RedisEventSubscription(channel="test.events.{value}")
    wildcard_subscription = RedisEventSubscription(channel="test.events.*")
    route = RedisEventRoute(channel="test.events.{value}")

    return Backend(
        name="redis",
        emitter=emitter,
        listener=listener,
        subscription=subscription,
        route=route,
        wildcard_subscription=wildcard_subscription
    )
