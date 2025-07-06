import pytest
import asyncio
from unittest.mock import AsyncMock
from dispytch.emitter.producer import ProducerTimeout
from dispytch.emitter.event import EventBase
from dispytch.emitter import EventEmitter


class DummyEvent(EventBase):
    __topic__ = "test-topic"
    __event_type__ = "dummy_event"


@pytest.mark.asyncio
async def test_emit_handles_timeout_and_calls_sync_on_timeout():
    producer = AsyncMock()
    producer.send.side_effect = ProducerTimeout()
    emitter = EventEmitter(producer)
    event = DummyEvent()

    called = False

    @emitter.on_timeout
    def on_timeout_sync(e):
        nonlocal called
        called = True
        assert e == event

    await emitter.emit(event)
    assert called


@pytest.mark.asyncio
async def test_emit_handles_timeout_and_awaits_async_on_timeout():
    producer = AsyncMock()
    producer.send.side_effect = ProducerTimeout()
    emitter = EventEmitter(producer)
    event = DummyEvent()

    called = False

    @emitter.on_timeout
    async def on_timeout_async(e):
        nonlocal called
        called = True
        assert e == event
        await asyncio.sleep(0.1)

    await emitter.emit(event)
    assert called
