import asyncio
import logging

from aiokafka import AIOKafkaConsumer

from dispytch import EventDispatcher
from dispytch.kafka import KafkaConsumer
from dispytch.serialization.json import JSONDeserializer

from .router import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    kafka_consumer = AIOKafkaConsumer('stress_test_events',
                                      bootstrap_servers='kafka:9092',
                                      enable_auto_commit=False,
                                      group_id='test_group', )
    await kafka_consumer.start()
    consumer = KafkaConsumer(kafka_consumer)
    event_listener = EventDispatcher(consumer, deserializer=JSONDeserializer())
    event_listener.add_router(router)
    logger.info("Consumer started")
    await event_listener.start()


if __name__ == '__main__':
    asyncio.run(main())
