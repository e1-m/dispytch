import pytest_asyncio
import aio_pika

from dispytch import EventEmitter, EventDispatcher
from dispytch.rabbitmq import RabbitMQProducer, RabbitMQConsumer, RabbitMQEventRoute, RabbitMQEventSubscription
from dispytch.serialization.msgpack import MessagePackSerializer, MessagePackDeserializer

from tests.integration.support.types import Backend


@pytest_asyncio.fixture()
def connection_string():
    return "amqp://guest:guest@localhost:5672"


@pytest_asyncio.fixture()
async def rabbitmq_connection(connection_string):
    connection = await aio_pika.connect(connection_string)
    yield connection
    await connection.close()


@pytest_asyncio.fixture()
async def rabbitmq_channel(rabbitmq_connection):
    channel = await rabbitmq_connection.channel()
    yield channel
    await channel.close()


@pytest_asyncio.fixture()
async def rabbitmq_exchange(rabbitmq_channel):
    exchange = await rabbitmq_channel.declare_exchange(
        'test_events',
        aio_pika.ExchangeType.DIRECT
    )
    yield exchange
    try:
        await exchange.delete()
    except Exception:
        pass


@pytest_asyncio.fixture()
async def rabbitmq_queue(rabbitmq_channel, rabbitmq_exchange):
    queue = await rabbitmq_channel.declare_queue('test_events')
    await queue.bind(rabbitmq_exchange, routing_key='test_events')
    yield queue
    try:
        await queue.delete()
    except Exception:
        pass


@pytest_asyncio.fixture()
async def producer_rabbitmq(rabbitmq_exchange):
    return RabbitMQProducer([rabbitmq_exchange])


@pytest_asyncio.fixture()
async def consumer_rabbitmq(rabbitmq_queue):
    consumer = RabbitMQConsumer(rabbitmq_queue)
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest_asyncio.fixture()
async def backend_rabbitmq(producer_rabbitmq, consumer_rabbitmq):
    emitter = EventEmitter(producer=producer_rabbitmq)
    listener = EventDispatcher(consumer=consumer_rabbitmq, route_delimiter='.')
    subscription = RabbitMQEventSubscription(routing_key="test_events")
    route = RabbitMQEventRoute(exchange="test_events", routing_key="test_events")

    return Backend(
        name="rabbitmq",
        emitter=emitter,
        listener=listener,
        subscription=subscription,
        route=route
    )


# --- Dynamic topics (subscription params) backend ---
@pytest_asyncio.fixture()
async def rabbitmq_exchange_params(rabbitmq_channel):
    exchange = await rabbitmq_channel.declare_exchange(
        'test_events',
        aio_pika.ExchangeType.TOPIC
    )
    yield exchange
    try:
        await exchange.delete()
    except Exception:
        pass


@pytest_asyncio.fixture()
async def rabbitmq_queue_params(rabbitmq_channel, rabbitmq_exchange_params):
    queue = await rabbitmq_channel.declare_queue('test_events')
    await queue.bind(rabbitmq_exchange_params, routing_key='test.events.*')
    yield queue
    try:
        await queue.delete()
    except Exception:
        pass


@pytest_asyncio.fixture()
async def producer_rabbitmq_params(rabbitmq_exchange_params):
    return RabbitMQProducer([rabbitmq_exchange_params])


@pytest_asyncio.fixture()
async def consumer_rabbitmq_params(rabbitmq_queue_params):
    consumer = RabbitMQConsumer(rabbitmq_queue_params)
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest_asyncio.fixture()
async def backend_rabbitmq_params(producer_rabbitmq_params, consumer_rabbitmq_params):
    emitter = EventEmitter(producer=producer_rabbitmq_params, serializer=MessagePackSerializer())
    listener = EventDispatcher(consumer=consumer_rabbitmq_params, deserializer=MessagePackDeserializer(),
                               route_delimiter='.')
    subscription = RabbitMQEventSubscription(routing_key="test.events.{value}")
    wildcard_subscription = RabbitMQEventSubscription(routing_key="test.events.*")
    route = RabbitMQEventRoute(exchange="test_events", routing_key="test.events.{value}")

    return Backend(
        name="rabbitmq",
        emitter=emitter,
        listener=listener,
        subscription=subscription,
        route=route,
        wildcard_subscription=wildcard_subscription
    )
