import pytest_asyncio
import aio_pika

from dispytch import EventEmitter, EventListener
from dispytch.rabbitmq import RabbitMQProducer, RabbitMQConsumer
from dispytch.serialization.msgpack import MessagePackSerializer, MessagePackDeserializer


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
        aio_pika.ExchangeType.TOPIC
    )
    yield exchange
    try:
        await exchange.delete()
    except Exception:
        pass


@pytest_asyncio.fixture()
async def rabbitmq_queue(rabbitmq_channel, rabbitmq_exchange):
    queue = await rabbitmq_channel.declare_queue('test_events')
    await queue.bind(rabbitmq_exchange, routing_key='test.events.*')
    yield queue
    try:
        await queue.delete()
    except Exception:
        pass


@pytest_asyncio.fixture()
async def dispytch_rabbitmq_producer(rabbitmq_exchange):
    return RabbitMQProducer(rabbitmq_exchange)


@pytest_asyncio.fixture()
async def dispytch_rabbitmq_consumer(rabbitmq_queue):
    return RabbitMQConsumer(rabbitmq_queue)


@pytest_asyncio.fixture()
async def emitter_rabbitmq(dispytch_rabbitmq_producer):
    return EventEmitter(
        producer=dispytch_rabbitmq_producer,
        serializer=MessagePackSerializer()
    )


@pytest_asyncio.fixture()
async def listener_rabbitmq(dispytch_rabbitmq_consumer):
    return EventListener(
        consumer=dispytch_rabbitmq_consumer,
        deserializer=MessagePackDeserializer(),
        topic_delimiter='.'
    )
