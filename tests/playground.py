import asyncio
from typing import Annotated

from aiokafka import AIOKafkaConsumer
from pydantic import BaseModel

from dispytch import EventListener, Event, Dependency
from dispytch.deserializers import JSONDeserializer
from dispytch.consumers import KafkaConsumer


class TestEventBody(BaseModel):
    test: int


async def test_inner(event: Event[TestEventBody]):
    print('test_inner entered')
    yield event.body.test
    print('test_inner exited')


async def test_outer(test: Annotated[int, Dependency(test_inner)], test2: Annotated[int, Dependency(test_inner)]):
    print('test_outer entered')
    yield 5 + test + test2
    print('test_outer exited')


async def main():
    kafka_consumer = AIOKafkaConsumer('test_events',
                                      bootstrap_servers='localhost:19092')
    consumer = KafkaConsumer(kafka_consumer, deserializer=JSONDeserializer())
    event_listener = EventListener(consumer)

    @event_listener.handler(topic='test_events', event='test_event')
    async def test_event_handler(event, test: Annotated[int, Dependency(test_outer)]):
        print(event)
        print(test)
        await asyncio.sleep(2)

    await event_listener.listen()


if __name__ == '__main__':
    asyncio.run(main())
