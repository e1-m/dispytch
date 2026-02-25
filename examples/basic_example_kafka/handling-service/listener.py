import asyncio

from aiokafka import AIOKafkaConsumer
from dispytch import EventDispatcher
from dispytch.kafka import KafkaConsumer

from routers import user_events


async def main():
    kafka_consumer = KafkaConsumer(
        AIOKafkaConsumer('user_events',
                         bootstrap_servers='localhost:19092',
                         enable_auto_commit=False,  # must be false, dispytch handles offsets
                         group_id='consumer_group_id',
                         auto_offset_reset='earliest'
                         )
    )
    await kafka_consumer.start()  # IMPORTANT! REMEMBER TO START THE CONSUMER.

    dispatcher = EventDispatcher(kafka_consumer)
    dispatcher.add_router(user_events)

    print("Starting dispatcher")
    await dispatcher.start()


if __name__ == '__main__':
    asyncio.run(main())
