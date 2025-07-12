import asyncio

from aiokafka import AIOKafkaProducer

from dispytch.kafka import KafkaProducer
from dispytch import EventEmitter, EventBase


class MyEvent(EventBase):
    __topic__ = 'test_events'
    __event_type__ = 'test_event'

    test: int


async def main():
    kafka_producer = AIOKafkaProducer(bootstrap_servers='localhost:19092')
    await kafka_producer.start()
    producer = KafkaProducer(kafka_producer)

    event_emitter = EventEmitter(producer)
    await asyncio.sleep(0.5)

    for i in range(10):
        await event_emitter.emit(MyEvent(test=i))
        print(f'Event {i} sent')
        await asyncio.sleep(0.3)


if __name__ == '__main__':
    asyncio.run(main())
