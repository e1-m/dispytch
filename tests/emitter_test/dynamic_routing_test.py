import pytest
from unittest.mock import AsyncMock
from dispytch.emitter.event import EventBase
from dispytch.emitter import EventEmitter
from dispytch.kafka import KafkaEventRoute
from dispytch.rabbitmq import RabbitMQEventRoute
from dispytch.redis import RedisEventRoute


@pytest.fixture
def mock_producer():
    return AsyncMock()


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_single_arg_kafka(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __route__ = KafkaEventRoute(
            topic="test:{value}",
        )

        value: int

    value = 1
    event = DummyEvent(
        value=value,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["route"].topic == f"test:{value}"


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_single_arg_redis(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __route__ = RedisEventRoute(
            channel="test:{value}",
        )

        value: int

    value = 1
    event = DummyEvent(
        value=value,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["route"].channel == f"test:{value}"


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_two_args_kafka(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __route__ = KafkaEventRoute(
            topic="test:{name}:{value}",
        )

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

    assert kwargs["route"].topic == f"test:{name}:{value}"


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_two_args_rabbitmq(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __route__ = RabbitMQEventRoute(
            exchange="test:{name}",
            routing_key="test:{value}",
        )

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

    assert kwargs["route"].exchange == f"test:{name}"
    assert kwargs["route"].routing_key == f"test:{value}"


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_two_same_args(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __route__ = KafkaEventRoute(
            topic="test:{value}:{value}",
        )

        value: int

    value = 1
    event = DummyEvent(
        value=value,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["route"].topic == f"test:{value}:{value}"


@pytest.mark.asyncio
async def test_emit_handles_runtime_topic_formating_with_nested_curly_braces(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __route__ = KafkaEventRoute(
            topic="test:{name}",
        )

        name: str

    name = "{something}"

    event = DummyEvent(
        name=name,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["route"].topic == f"test:{name}"


@pytest.mark.asyncio
async def test_emit_differentiate_dynamic_and_static_segments(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __route__ = KafkaEventRoute(
            topic="test:name:{name}",
        )

        name: str

    name = "qwerty"

    event = DummyEvent(
        name=name,
    )
    await emitter.emit(event)

    args, kwargs = mock_producer.send.call_args

    assert kwargs["route"].topic == f"test:name:{name}"


@pytest.mark.asyncio
async def test_emit_throws_with_malformed_topic(mock_producer):
    emitter = EventEmitter(mock_producer)

    class DummyEvent(EventBase):
        __route__ = KafkaEventRoute(
            topic="test:{}",
        )

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
        __route__ = KafkaEventRoute(
            topic="test:{value}",
        )

        name: str

    event = DummyEvent(
        name="something",
    )

    with pytest.raises(RuntimeError):
        await emitter.emit(event)
