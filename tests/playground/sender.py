import asyncio

from aiokafka import AIOKafkaProducer

from dispytch.producers import KafkaProducer
from dispytch.serializers import JSONSerializer
from dispytch import EventEmitter, EventBase


class MyEvent(EventBase):
    __topic__ = 'test_events'
    __event_type__ = 'test_event'

    test: int


async def main():
    kafka_producer = AIOKafkaProducer(bootstrap_servers='localhost:19092')
    producer = KafkaProducer(kafka_producer, serializer=JSONSerializer())
    await producer.start()

    event_emitter = EventEmitter(producer)
    await asyncio.sleep(0.5)

    for i in range(10):
        await event_emitter.emit(MyEvent(test=i))
        print(f'Event {i} sent')
        await asyncio.sleep(0.3)

    await producer.stop()


if __name__ == '__main__':
    asyncio.run(main())
