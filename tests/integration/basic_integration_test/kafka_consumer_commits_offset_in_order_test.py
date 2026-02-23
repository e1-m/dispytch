import asyncio
from typing import Callable, Awaitable

import pytest
from pydantic import BaseModel

from dispytch import EventBase, Event, EventEmitter, EventDispatcher, Dependency, EventSubscription
from dispytch.emitter.producer import EventRoute

from tests.integration.basic_integration_test.kafka_setup import *


class MyEvent(EventBase):
    id: int


class MyEventBody(BaseModel):
    id: int


@pytest.fixture(scope="function")
def emitter(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def listener(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def subscription(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def route(request):
    return request.getfixturevalue(request.param)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("emitter", "listener", "subscription", "route", "get_committed_offset"),
    [
        ("emitter_kafka", "listener_kafka", "subscription_kafka", "event_route_kafka", "get_committed_offset"),
    ],
    indirect=True,
)
async def test_consumer_commits_offset_in_order(
        emitter: EventEmitter,
        listener: EventDispatcher,
        subscription: EventSubscription,
        route: EventRoute,
        get_committed_offset: Callable[[], Awaitable[int]]
):
    number_of_events = 3

    started_events = {i: asyncio.Event() for i in range(1, number_of_events + 1)}
    proceed_events = {i: asyncio.Event() for i in range(1, number_of_events + 1)}

    received_queue = asyncio.Queue()

    @listener.handler(subscription)
    async def handle_event(event: Event[MyEventBody]):
        started_events[event.id].set()

        await proceed_events[event.id].wait()

        await received_queue.put(event)

    for i in range(1, number_of_events + 1):
        test_event = MyEvent(id=i)
        test_event.__route__ = route
        await emitter.emit(test_event)
        await asyncio.sleep(0.1)

    listener_task = asyncio.create_task(listener.start())

    try:
        await asyncio.wait_for(
            asyncio.gather(*(e.wait() for e in started_events.values())),
            timeout=5.0
        )

        prev_offset = await get_committed_offset()

        # complete Event 3
        proceed_events[3].set()
        processed_event = await asyncio.wait_for(received_queue.get(), timeout=1.0)
        assert processed_event.id == 3

        # assert not committed
        await asyncio.sleep(0.1)
        assert await get_committed_offset() == prev_offset

        # complete Event 1
        proceed_events[1].set()
        processed_event = await asyncio.wait_for(received_queue.get(), timeout=1.0)
        assert processed_event.id == 1

        # assert committed Event 1
        await asyncio.sleep(0.1)
        assert await get_committed_offset() == prev_offset + 1

        # complete Event 2
        proceed_events[2].set()
        processed_event = await asyncio.wait_for(received_queue.get(), timeout=1.0)
        assert processed_event.id == 2

        # assert committed Event 2 and Event 3
        await asyncio.sleep(0.1)
        assert await get_committed_offset() == prev_offset + 3

    finally:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
