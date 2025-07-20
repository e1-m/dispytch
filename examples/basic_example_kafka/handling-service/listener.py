import asyncio

from aiokafka import AIOKafkaConsumer
from dispytch import EventListener
from dispytch.kafka import KafkaConsumer

from handlers import user_events


async def main():
    kafka_consumer = AIOKafkaConsumer('user_events',
                                      bootstrap_servers='localhost:19092',
                                      enable_auto_commit=False,
                                      group_id='consumer_group_id', )
    await kafka_consumer.start()  # DO NOT FORGET THIS LINE.
    # Without it, you'll be staring at an empty console as nothing is gonna be consumed before the consumer starts

    listener = EventListener(KafkaConsumer(kafka_consumer))
    listener.add_handler_group(user_events)

    await listener.listen()


if __name__ == '__main__':
    asyncio.run(main())
