import asyncio
from typing import Annotated

from aiokafka import AIOKafkaConsumer
from pydantic import BaseModel

from dispytch import EventListener, Event, Dependency
from dispytch.kafka import KafkaConsumer


class MyEventBody(BaseModel):
    test: int


async def inner_dep(event: Event[MyEventBody]):
    print('inner_dep entered')
    yield event.body.test
    print('inner_dep exited')


async def outer_dep(test: Annotated[int, Dependency(inner_dep)],
                    test2: Annotated[int, Dependency(inner_dep)]):
    print('outer_dep entered')
    yield 5 + test + test2
    print('outer_dep exited')


async def main():
    kafka_consumer = AIOKafkaConsumer('test_events',
                                      bootstrap_servers='localhost:19092',
                                      enable_auto_commit=False,
                                      group_id='test_group', )
    consumer = KafkaConsumer(kafka_consumer)
    event_listener = EventListener(consumer)

    @event_listener.handler(topic='test_events', event='test_event')
    async def handle_event(event: Event[MyEventBody], test: Annotated[int, Dependency(outer_dep)]):
        print(event)
        print(test)
        await asyncio.sleep(2)

    await event_listener.listen()


if __name__ == '__main__':
    asyncio.run(main())
