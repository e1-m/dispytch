import asyncio

import pytest
from pydantic import BaseModel
from typing import Annotated

from dispytch import EventBase, Event, EventEmitter, EventListener, Dependency

from tests.integration.kafka_setup import *
from tests.integration.rabbitmq_setup import *


class MyEvent(EventBase):
    __topic__ = 'test_events'
    __event_type__ = 'test_event'

    value: int
    message: str


class MyEventBody(BaseModel):
    value: int
    message: str


listener_start_up_time = 0.3
event_processing_delay = 0.5


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
    ],
    indirect=True,
)
async def test_kafka_emit_and_receive(emitter: EventEmitter, listener: EventListener):
    """Test basic event emission and reception with Kafka."""
    received_events = []

    @listener.handler(topic='test_events', event='test_event')
    async def handle_event(event: Event[MyEventBody]):
        received_events.append(event)

    listener_task = asyncio.create_task(listener.listen())
    await asyncio.sleep(listener_start_up_time)

    test_event = MyEvent(value=42, message="test message")

    await emitter.emit(test_event)

    await asyncio.sleep(event_processing_delay)

    try:
        listener_task.cancel()
        await listener_task
    except asyncio.CancelledError:
        pass

    assert len(received_events) == 1
    assert received_events[0].body.value == test_event.value
    assert received_events[0].body.message == test_event.message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("emitter", "listener"),
    [
        ("emitter_kafka", "listener_kafka"),
        ("emitter_rabbitmq", "listener_rabbitmq"),
    ],
    indirect=True,
)
async def test_kafka_multiple_events(emitter: EventEmitter, listener: EventListener):
    """Test handling multiple events in sequence."""
    received_events = []

    @listener.handler(topic='test_events', event='test_event')
    async def handle_event(event: Event[MyEventBody]):
        received_events.append(event)
        await asyncio.sleep(0.3)

    listener_task = asyncio.create_task(listener.listen())

    await asyncio.sleep(listener_start_up_time)

    num_events = 20
    for i in range(num_events):
        test_event = MyEvent(value=i, message=f"test message {i}")
        await emitter.emit(test_event)

    await asyncio.sleep(event_processing_delay)

    try:
        listener_task.cancel()
        await listener_task
    except asyncio.CancelledError:
        pass

    assert len(received_events) == num_events
    for i in range(num_events):
        assert received_events[i].body.value == i
        assert received_events[i].body.message == f"test message {i}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("emitter", "listener"),
    [
        ("emitter_kafka", "listener_kafka"),
        ("emitter_rabbitmq", "listener_rabbitmq"),
    ],
    indirect=True,
)
async def test_kafka_handler_with_retries(emitter: EventEmitter, listener: EventListener):
    """Test handler retry functionality."""
    attempts = []

    @listener.handler(topic='test_events', event='test_event', retries=2, retry_interval_sec=0)
    async def handle_event_with_retries(event: Event[MyEventBody]):
        attempts.append(1)
        if len(attempts) <= 2:
            raise ValueError("Simulated failure")
        return "success"

    listener_task = asyncio.create_task(listener.listen())

    await asyncio.sleep(listener_start_up_time)

    test_event = MyEvent(value=42, message="retry test")
    await emitter.emit(test_event)

    await asyncio.sleep(event_processing_delay)

    try:
        listener_task.cancel()
        await listener_task
    except asyncio.CancelledError:
        pass

    assert len(attempts) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("emitter", "listener"),
    [
        ("emitter_kafka", "listener_kafka"),
        ("emitter_rabbitmq", "listener_rabbitmq"),
    ],
    indirect=True,
)
async def test_kafka_handler_with_dependencies(emitter: EventEmitter, listener: EventListener):
    """Test dependency injection in handlers."""
    results = []

    async def value_provider(event: Event[MyEventBody]):
        return event.body.value * 2

    async def message_provider(event: Event[MyEventBody]):
        return f"Processed: {event.body.message}"

    @listener.handler(topic='test_events', event='test_event')
    async def handle_event_with_deps(
            event: Event[MyEventBody],
            doubled_value: Annotated[int, Dependency(value_provider)],
            processed_message: Annotated[str, Dependency(message_provider)]
    ):
        results.append({
            "original_value": event.body.value,
            "doubled_value": doubled_value,
            "processed_message": processed_message
        })

    listener_task = asyncio.create_task(listener.listen())

    await asyncio.sleep(listener_start_up_time)

    test_event = MyEvent(value=21, message="dependency test")
    await emitter.emit(test_event)

    await asyncio.sleep(event_processing_delay)

    try:
        listener_task.cancel()
        await listener_task
    except asyncio.CancelledError:
        pass

    assert len(results) == 1
    assert results[0]["original_value"] == 21
    assert results[0]["doubled_value"] == 42
    assert results[0]["processed_message"] == "Processed: dependency test"
