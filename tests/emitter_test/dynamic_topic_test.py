import pytest
from unittest.mock import AsyncMock
from dispytch.emitter.event import EventBase
from dispytch.emitter import EventEmitter


@pytest.fixture
def mock_producer():
    return AsyncMock()


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_single_arg(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __topic__ = "test:{value}"
        __event_type__ = "dummy_event"

        value: int

    value = 1
    event = DummyEvent(
        value=value,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["topic"] == f"test:{value}"


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_two_args(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __topic__ = "test:{name}:{value}"
        __event_type__ = "dummy_event"

        value: int
        name: str

    value = 1
    name = "something"

    event = DummyEvent(
        value=value,
        name=name,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["topic"] == f"test:{name}:{value}"


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_two_same_args(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __topic__ = "test:{value}:{value}"
        __event_type__ = "dummy_event"

        value: int

    value = 1
    event = DummyEvent(
        value=value,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["topic"] == f"test:{value}:{value}"


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_nested_curly_braces(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __topic__ = "test:{name}"
        __event_type__ = "dummy_event"

        name: str

    name = "{something}"

    event = DummyEvent(
        name=name,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["topic"] == f"test:{name}"


@pytest.mark.asyncio
async def test_emit_differentiate_dynamic_and_static_segments(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __topic__ = "test:name:{name}"
        __event_type__ = "dummy_event"

        name: str

    name = "qwerty"

    event = DummyEvent(
        name=name,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["topic"] == f"test:name:{name}"


@pytest.mark.asyncio
async def test_emit_throws_with_malformed_topic(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __topic__ = "test:{}"
        __event_type__ = "dummy_event"

        value: int

    value = 1
    event = DummyEvent(
        value=value,
    )
    with pytest.raises(RuntimeError):
        await emitter.emit(event)


@pytest.mark.asyncio
async def test_emit_throws_with_missing_arg(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __topic__ = "test:{value}"
        __event_type__ = "dummy_event"

        name: str

    event = DummyEvent(
        name="something",
    )

    with pytest.raises(RuntimeError):
        await emitter.emit(event)
