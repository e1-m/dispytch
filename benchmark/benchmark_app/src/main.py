import asyncio
import logging

from aiokafka import AIOKafkaConsumer
from prometheus_client import start_http_server

from dispytch import EventDispatcher
from dispytch.kafka import KafkaConsumer
from dispytch.serialization.json import JSONDeserializer

from .middleware import EventsInProgressMiddleware, LatencyMiddleware, TotalCounterMiddleware
from .config import config

if config.SCENARIO == "raw":
    from .routers.raw_throughput import router
elif config.SCENARIO == "with-io":
    from .routers.io_simulation import router
elif config.SCENARIO == "with-resource-pool":
    from .routers.resource_pool_simulation import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    kafka_consumer = AIOKafkaConsumer(
        'benchmark_events',
        bootstrap_servers='kafka:9092',
        enable_auto_commit=False,
        group_id='test_group',
        auto_offset_reset='earliest',
        fetch_max_bytes=(
                (config.MESSAGE_SIZE_BYTES * 2)
                * config.IN_FLIGHT_MSG_LIMIT_PER_PARTITION
                * config.KAFKA_PARTITIONS
        ),
        max_partition_fetch_bytes=(config.MESSAGE_SIZE_BYTES * 2) * config.IN_FLIGHT_MSG_LIMIT_PER_PARTITION,
    )

    consumer = KafkaConsumer(kafka_consumer,
                             batch_timeout_ms=config.BATCH_COMMIT_TIMEOUT_MS,
                             batch_size=config.BATCH_COMMIT_BATCH_SIZE,
                             fetch_interval_ms=config.FETCH_INTERVAL_MS,
                             in_flight_msg_limit_per_partition=config.IN_FLIGHT_MSG_LIMIT_PER_PARTITION)

    event_listener = EventDispatcher(consumer,
                                     deserializer=JSONDeserializer(),
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
