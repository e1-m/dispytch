import pytest_asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from dispytch import EventEmitter, EventDispatcher
from dispytch.kafka import KafkaProducer, KafkaConsumer, KafkaEventRoute, KafkaEventSubscription
from dispytch.serialization.msgpack import MessagePackSerializer, MessagePackDeserializer

from tests.integration.support.types import Backend


@pytest_asyncio.fixture()
async def bootstrap_servers():
    return 'localhost:19092'


@pytest_asyncio.fixture()
async def topics():
    return ['test_events']


@pytest_asyncio.fixture()
async def kafka_consumer(topics, bootstrap_servers):
    consumer = AIOKafkaConsumer(*topics,
                                bootstrap_servers=bootstrap_servers,
                                group_id='test_group',
                                enable_auto_commit=False,
                                auto_offset_reset='earliest')
    yield consumer


@pytest_asyncio.fixture()
async def kafka_producer(bootstrap_servers):
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
    )
    await producer.start()
    yield producer
    await producer.stop()


@pytest_asyncio.fixture()
async def producer_kafka(kafka_producer: AIOKafkaProducer):
    return KafkaProducer(kafka_producer)


@pytest_asyncio.fixture()
async def consumer_kafka(kafka_consumer: AIOKafkaConsumer):
    consumer = KafkaConsumer(kafka_consumer, batch_size=1)
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest_asyncio.fixture()
async def get_committed_offset(topics, consumer_kafka):
    tps = consumer_kafka.consumer.assignment()
    if len(tps) != 1:
        raise ValueError("Consumer is not assigned to a single topic")

    async def inner():
        tp = next(iter(tps))
        offset = await consumer_kafka.consumer.committed(tp)
        return offset if offset is not None else 0

    return inner


@pytest_asyncio.fixture()
async def backend_kafka(producer_kafka, consumer_kafka, topics, get_committed_offset):
    emitter = EventEmitter(producer=producer_kafka)
    listener = EventDispatcher(consumer=consumer_kafka, route_delimiter='.')
    subscription = KafkaEventSubscription(topic=topics[0])
    route = KafkaEventRoute(topic=topics[0])

    return Backend(
        name="kafka",
        emitter=emitter,
        listener=listener,
        subscription=subscription,
        route=route,
        get_committed_offset=get_committed_offset
    )


# --- Dynamic topics (subscription params) backend ---
@pytest_asyncio.fixture()
async def topics_params():
    return ['test.events.0', 'test.events.1', 'test.events.2']


@pytest_asyncio.fixture()
async def kafka_consumer_params(bootstrap_servers, topics_params):
    consumer = AIOKafkaConsumer(*topics_params,
                                bootstrap_servers=bootstrap_servers,
                                group_id='test_group',
                                enable_auto_commit=False,
                                auto_offset_reset='earliest')
    yield consumer


@pytest_asyncio.fixture()
async def kafka_producer_params(bootstrap_servers):
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
    )
    await producer.start()
    yield producer
    await producer.stop()


@pytest_asyncio.fixture()
async def producer_kafka_params(kafka_producer_params: AIOKafkaProducer):
    return KafkaProducer(kafka_producer_params)


@pytest_asyncio.fixture()
async def consumer_kafka_params(kafka_consumer_params: AIOKafkaConsumer):
    consumer = KafkaConsumer(kafka_consumer_params, batch_size=1)
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest_asyncio.fixture()
async def backend_kafka_params(producer_kafka_params, consumer_kafka_params):
    emitter = EventEmitter(producer=producer_kafka_params, serializer=MessagePackSerializer())
    listener = EventDispatcher(consumer=consumer_kafka_params, deserializer=MessagePackDeserializer(),
                               route_delimiter='.')
    subscription = KafkaEventSubscription(topic="test.events.{value}")
    wildcard_subscription = KafkaEventSubscription(topic="test.events.*")
    route = KafkaEventRoute(topic="test.events.{value}")

    return Backend(
        name="kafka",
        emitter=emitter,
        listener=listener,
        subscription=subscription,
        route=route,
        wildcard_subscription=wildcard_subscription
    )
