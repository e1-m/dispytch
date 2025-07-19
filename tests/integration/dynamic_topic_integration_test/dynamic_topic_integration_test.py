import asyncio
from typing import Annotated

import pytest
from pydantic import BaseModel

from dispytch import EventBase, Event
from dispytch.di.topic_segment import TopicSegment
from tests.integration.dynamic_topic_integration_test.redis_setup import *
from tests.integration.dynamic_topic_integration_test.kafka_setup import *
from tests.integration.dynamic_topic_integration_test.rabbitmq_setup import *


class MyEventBody(BaseModel):
    value: int
    message: str


class MyEventDynamicTopic(EventBase):
    __topic__ = 'test.events.{value}'
    __event_type__ = 'test_event'

    value: int
    message: str


listener_start_up_time = 0.5
event_processing_delay = 1


@pytest.fixture
def emitter(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def listener(request):
    return request.getfixturevalue(request.param)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("emitter", "listener"),
    [
        ("emitter_kafka", "listener_kafka"),
        ("emitter_rabbitmq", "listener_rabbitmq"),
        ("emitter_redis", "listener_redis"),
    ],
    indirect=True,
)
async def test_dynamic_topics(emitter: EventEmitter, listener: EventListener):
    """Test handling multiple events with dynamic topics"""
    received_values = []

    @listener.handler(topic='test.events.{value}', event='test_event')
    async def handle_event(value: Annotated[int, TopicSegment()]):
        received_values.append(value)
        await asyncio.sleep(0.3)

    listener_task = asyncio.create_task(listener.listen())

    await asyncio.sleep(listener_start_up_time)

    num_events = 3
    for i in range(num_events):
        test_event = MyEventDynamicTopic(value=i, message=f"test message {i}")
        await emitter.emit(test_event)

    await asyncio.sleep(event_processing_delay)

    try:
        listener_task.cancel()
        await listener_task
    except asyncio.CancelledError:
        pass

    assert len(received_values) == num_events
    assert set(received_values) == set(range(num_events))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("emitter", "listener"),
    [
        ("emitter_kafka", "listener_kafka"),
        ("emitter_rabbitmq", "listener_rabbitmq"),
        ("emitter_redis", "listener_redis"),
    ],
    indirect=True,
)
async def test_dynamic_wildcard_topics(emitter: EventEmitter, listener: EventListener):
    """Test handling multiple events with a wildcard topic"""
    received_values = []

    @listener.handler(topic='test.events.*', event='test_event')
    async def handle_event(event: Event[MyEventBody]):
        received_values.append(event.body.value)
        await asyncio.sleep(0.3)

    listener_task = asyncio.create_task(listener.listen())

    await asyncio.sleep(listener_start_up_time)

    num_events = 3
    for i in range(num_events):
        test_event = MyEventDynamicTopic(value=i, message=f"test message {i}")
        await emitter.emit(test_event)

    await asyncio.sleep(event_processing_delay)

    try:
        listener_task.cancel()
        await listener_task
    except asyncio.CancelledError:
        pass

    assert len(received_values) == num_events
    assert set(received_values) == set(range(num_events))
