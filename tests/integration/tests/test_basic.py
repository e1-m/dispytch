import pytest
from pydantic import BaseModel
from typing import Annotated

from dispytch import Event, Dependency, EventBase
from dispytch.middleware.retry import ExponentialBackoffWithFullJitter, Retry

from tests.integration.support.lifecycle import running_listener
from tests.integration.support.helpers import assert_eventually


class MyEventBody(BaseModel):
    value: int
    message: str


class MyEvent(EventBase):
    value: int
    message: str


@pytest.mark.asyncio
async def test_emit_and_receive(backend):
    received = []

    @backend.listener.handler(backend.subscription)
    async def handle(event: Event[MyEventBody]):
        received.append(event)

    async with running_listener(backend.listener):
        test_event = MyEvent(value=42, message="hello")
        test_event.__route__ = backend.route
        await backend.emitter.emit(test_event)

        async def check():
            assert len(received) == 1

        await assert_eventually(check)

    assert received[0].value == 42


@pytest.mark.asyncio
async def test_retry_middleware(backend):
    attempts = []

    retry_policy = ExponentialBackoffWithFullJitter(
        retries=2,
        base_delay_sec=0.1,
        max_delay_sec=0.2
    )

    @backend.listener.handler(backend.subscription, middlewares=[Retry(retry_policy)])
    async def handle(event: Event[MyEventBody]):
        attempts.append(event)
        raise ValueError("Simulated failure")

    async with running_listener(backend.listener):
        test_event = MyEvent(value=42, message="retry test")
        test_event.__route__ = backend.route
        await backend.emitter.emit(test_event)

        async def check():
            assert len(attempts) == 3

        await assert_eventually(check, timeout=5)


@pytest.mark.asyncio
async def test_handler_with_dependencies(backend):
    results = []

    async def value_provider(event: Event[MyEventBody]):
        return event.value * 2

    async def message_provider(event: Event[MyEventBody]):
        return f"Processed: {event.message}"

    @backend.listener.handler(backend.subscription)
    async def handle_event_with_deps(
            event: Event[MyEventBody],
            doubled_value: Annotated[int, Dependency(value_provider)],
            processed_message: Annotated[str, Dependency(message_provider)]
    ):
        results.append({
            "original_value": event.value,
            "doubled_value": doubled_value,
            "processed_message": processed_message
        })

    async with running_listener(backend.listener):
        test_event = MyEvent(value=21, message="dependency test")
        test_event.__route__ = backend.route
        await backend.emitter.emit(test_event)

        async def check():
            assert len(results) == 1

        await assert_eventually(check)

    assert results[0]["original_value"] == 21
    assert results[0]["doubled_value"] == 42
    assert results[0]["processed_message"] == "Processed: dependency test"
