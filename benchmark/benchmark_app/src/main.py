import asyncio
import logging

from aiokafka import AIOKafkaConsumer
from prometheus_client import start_http_server

from dispytch import EventDispatcher
from dispytch.kafka import KafkaConsumer
from dispytch.serialization.orjson import ORJSONDeserializer

from .raw_throughput import router
from .middleware import EventsInProgressMiddleware, LatencyMiddleware, TotalCounterMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    kafka_consumer = AIOKafkaConsumer('benchmark_events',
                                      bootstrap_servers='kafka:9092',
                                      enable_auto_commit=False,
                                      group_id='test_group',
                                      fetch_max_bytes=1024 * 1000 * 10,
                                      max_partition_fetch_bytes=1024 * 1000,
                                      )

    consumer = KafkaConsumer(kafka_consumer,
                             batch_timeout_ms=5000,
                             fetch_interval_ms=50,
                             batch_size=500,
                             in_flight_msg_limit_per_partition=500)

    event_listener = EventDispatcher(consumer,
                                     deserializer=ORJSONDeserializer(),
                                     middlewares=[EventsInProgressMiddleware(),
                                                  LatencyMiddleware(),
                                                  TotalCounterMiddleware()])
    event_listener.add_router(router)

    await consumer.start()
    start_http_server(8080)
    logger.info("Consumer started")
    await event_listener.start()


if __name__ == '__main__':
    asyncio.run(main())
