import pytest_asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from dispytch import EventEmitter, EventListener
from dispytch.kafka import KafkaProducer, KafkaConsumer

from dispytch.serialization.msgpack import MessagePackSerializer, MessagePackDeserializer


@pytest_asyncio.fixture()
async def bootstrap_servers():
    return 'localhost:19092'


@pytest_asyncio.fixture()
async def topics(bootstrap_servers):
    return ['test.events.0', 'test.events.1', 'test.events.2']


@pytest_asyncio.fixture()
async def kafka_consumer(bootstrap_servers, topics):
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
async def dispytch_kafka_producer(kafka_producer: AIOKafkaProducer):
    return KafkaProducer(kafka_producer)


@pytest_asyncio.fixture()
async def dispytch_kafka_consumer(kafka_consumer: AIOKafkaConsumer):
    return KafkaConsumer(kafka_consumer)


@pytest_asyncio.fixture()
async def emitter_kafka(dispytch_kafka_producer):
    return EventEmitter(
        producer=dispytch_kafka_producer,
        serializer=MessagePackSerializer(),
    )


@pytest_asyncio.fixture()
async def listener_kafka(dispytch_kafka_consumer):
    return EventListener(
        consumer=dispytch_kafka_consumer,
        deserializer=MessagePackDeserializer(),
        topic_delimiter='.'
    )
