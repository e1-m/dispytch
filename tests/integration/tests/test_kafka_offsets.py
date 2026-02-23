import asyncio
import pytest
from typing import Callable, Awaitable
from pydantic import BaseModel

from dispytch import Event, EventBase

from tests.integration.support.lifecycle import running_listener


class MyEvent(EventBase):
    id: int


class MyEventBody(BaseModel):
    id: int


@pytest.mark.asyncio
async def test_consumer_commits_offset_in_order(backend_kafka, get_committed_offset: Callable[[], Awaitable[int]]):
    backend = backend_kafka
    number_of_events = 3

    started_events = {i: asyncio.Event() for i in range(1, number_of_events + 1)}
    proceed_events = {i: asyncio.Event() for i in range(1, number_of_events + 1)}

    received_queue = asyncio.Queue()

    @backend.listener.handler(backend.subscription)
    async def handle_event(event: Event[MyEventBody]):
        started_events[event.id].set()
        await proceed_events[event.id].wait()
        await received_queue.put(event)

    # Emit events before starting listener to ensure they are in the queue
    for i in range(1, number_of_events + 1):
        test_event = MyEvent(id=i)
        test_event.__route__ = backend.route
        await backend.emitter.emit(test_event)
        await asyncio.sleep(0.1)

    async with running_listener(backend.listener):
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
