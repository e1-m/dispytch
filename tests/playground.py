import asyncio
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer

from src.consumer import KafkaConsumer
from src.deserializer import JSONDeserializer
from src.event_listener import EventListener


@asynccontextmanager
async def test_dep():
    print('test_dep entered')
    yield 5
    print('test_dep exited')


async def main():
    kafka_consumer = AIOKafkaConsumer('test_events',
                                      bootstrap_servers='localhost:19092')
    consumer = KafkaConsumer(kafka_consumer, deserializer=JSONDeserializer())
    event_listener = EventListener(consumer)

    @event_listener.handler(topic='test_events', event='test_event', inject={'test': test_dep})
    async def test_event_handler(event, test):
        print(event)
        print(test)
        await asyncio.sleep(5)

    await event_listener.listen()


if __name__ == '__main__':
    asyncio.run(main())
