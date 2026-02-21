import pytest_asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from dispytch import EventEmitter, EventDispatcher
from dispytch.kafka import KafkaProducer, KafkaConsumer, KafkaEventRoute, KafkaEventSubscription


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
async def emitter_kafka(producer_kafka):
    return EventEmitter(
        producer=producer_kafka
    )


@pytest_asyncio.fixture()
async def listener_kafka(consumer_kafka):
    return EventDispatcher(
        consumer=consumer_kafka,
    )


@pytest_asyncio.fixture()
async def subscription_kafka(topics):
    return KafkaEventSubscription(
        topic=topics[0]
    )


@pytest_asyncio.fixture()
async def event_route_kafka(topics):
    return KafkaEventRoute(
        topic=topics[0]
    )
