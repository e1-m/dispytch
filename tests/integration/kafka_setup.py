import pytest_asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from dispytch import EventEmitter, EventListener
from dispytch.producers import KafkaProducer
from dispytch.consumers import KafkaConsumer


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
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest_asyncio.fixture()
async def kafka_producer(bootstrap_servers):
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
    )
    await producer.start()
    yield producer
    await producer.stop()


@pytest_asyncio.fixture()
async def producer(kafka_producer: AIOKafkaProducer):
    return KafkaProducer(kafka_producer)


@pytest_asyncio.fixture()
async def consumer(kafka_consumer: AIOKafkaConsumer):
    return KafkaConsumer(kafka_consumer)


@pytest_asyncio.fixture()
async def emitter_kafka(producer):
    return EventEmitter(
        producer=producer
    )


@pytest_asyncio.fixture()
async def listener_kafka(consumer):
    return EventListener(
        consumer=consumer,
    )
