import asyncio
import pytest
from pydantic import BaseModel

from dispytch import EventBase, SubscriptionParam, Event
from tests.integration.support.lifecycle import running_listener
from tests.integration.support.helpers import assert_eventually


class MyEventDynamicTopic(EventBase):
    value: int
    message: str


class MyEventDynamicTopicBody(BaseModel):
    value: int
    message: str


@pytest.mark.asyncio
async def test_dynamic_topics(backend_params):
    received_values = []

    @backend_params.listener.handler(backend_params.subscription)
    async def handle_event(value: int = SubscriptionParam()):
        received_values.append(value)
        await asyncio.sleep(0.05)

    async with running_listener(backend_params.listener):
        num_events = 3
        for i in range(num_events):
            test_event = MyEventDynamicTopic(value=i, message=f"test message {i}")
            test_event.__route__ = backend_params.route
            await backend_params.emitter.emit(test_event)

        async def check():
            assert len(received_values) == num_events
            assert set(received_values) == set(range(num_events))

        await assert_eventually(check, timeout=5)


@pytest.mark.asyncio
async def test_dynamic_wildcard_topics(backend_params):
    received_values = []

    @backend_params.listener.handler(backend_params.wildcard_subscription)
    async def handle_event(event: Event[MyEventDynamicTopicBody]):
        received_values.append(event.value)
        await asyncio.sleep(0.05)

    async with running_listener(backend_params.listener):
        num_events = 3
        for i in range(num_events):
            test_event = MyEventDynamicTopic(value=i, message=f"test message {i}")
            test_event.__route__ = backend_params.route
            await backend_params.emitter.emit(test_event)

        async def check():
            assert len(received_values) == num_events
            assert set(received_values) == set(range(num_events))

        await assert_eventually(check, timeout=5)
