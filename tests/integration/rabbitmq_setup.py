import pytest_asyncio
import aio_pika

from dispytch import EventEmitter, EventListener
from dispytch.producers import RabbitMQProducer
from dispytch.consumers import RabbitMQConsumer


@pytest_asyncio.fixture()
def connection_string():
    host = 'localhost'
    port = 5672

    connection_string = f"amqp://guest:guest@{host}:{port}"

    return connection_string


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
async def producer(rabbitmq_exchange):
    return RabbitMQProducer(rabbitmq_exchange)


@pytest_asyncio.fixture()
async def consumer(rabbitmq_queue):
    return RabbitMQConsumer(rabbitmq_queue)


@pytest_asyncio.fixture()
async def emitter_rabbitmq(producer):
    return EventEmitter(
        producer=producer
    )


@pytest_asyncio.fixture()
async def listener_rabbitmq(consumer):
    return EventListener(
        consumer=consumer,
    )
