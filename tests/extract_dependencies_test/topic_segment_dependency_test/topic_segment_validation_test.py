import uuid
from decimal import Decimal
from typing import Annotated, Literal

import pytest

from dispytch import Dependency
from dispytch.di.extractor import extract_dependencies
from dispytch.di.context import EventHandlerContext
from dispytch.di.event import Event
from dispytch.di.topic_segment import TopicSegment


@pytest.fixture
def event_dict():
    return Event(**{
        'id': str(uuid.uuid4()),
        'topic': 'test:topic:123',
        'type': 'test-type',
        'body': {
            'name': 'test',
            'value': 42
        },
        'timestamp': 100
    })


@pytest.mark.asyncio
async def test_literal_validation_success(event_dict):
    def func(value: Annotated[Literal["test", "example", "123"], TopicSegment()]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=EventHandlerContext(event=event_dict,
                                           topic_pattern="test:topic:{value}",
                                           topic_delimiter=':')) as param:
        assert isinstance(param, str)
        assert param == "123"


@pytest.mark.asyncio
async def test_literal_validation_failure(event_dict):
    def func(value: Annotated[Literal["test", "example"], TopicSegment()]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=EventHandlerContext(event=event_dict,
                                    topic_pattern="test:topic:{value}",
                                    topic_delimiter=':')
            )


@pytest.mark.asyncio
async def test_int_validation_success(event_dict):
    def func(value: Annotated[int, TopicSegment(le=125)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=EventHandlerContext(event=event_dict,
                                           topic_pattern="test:topic:{value}",
                                           topic_delimiter=':')) as param:
        assert isinstance(param, int)
        assert param == 123


@pytest.mark.asyncio
async def test_int_validation_failure(event_dict):
    def func(value: Annotated[int, TopicSegment(le=100)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=EventHandlerContext(event=event_dict,
                                    topic_pattern="test:topic:{value}",
                                    topic_delimiter=':')
            )


@pytest.mark.asyncio
async def test_str_validation_success(event_dict):
    def func(value: Annotated[str, TopicSegment(min_length=1)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=EventHandlerContext(event=event_dict,
                                           topic_pattern="test:topic:{value}",
                                           topic_delimiter=':')) as param:
        assert isinstance(param, str)
        assert param == "123"


@pytest.mark.asyncio
async def test_str_validation_failure(event_dict):
    def func(value: Annotated[str, TopicSegment(min_length=10)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=EventHandlerContext(event=event_dict,
                                    topic_pattern="test:topic:{value}",
                                    topic_delimiter=':'))


@pytest.mark.asyncio
async def test_str_validation_inappropriate_constrains(event_dict):
    def func(value: Annotated[str, TopicSegment(le=100)]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(TypeError):
        dep(ctx=EventHandlerContext(event=event_dict,
                                    topic_pattern="test:topic:{value}",
                                    topic_delimiter=':'))


@pytest.mark.asyncio
async def test_decimal_validation_success(event_dict):
    event_dict.topic = 'test:topic:123.45'

    def func(value: Annotated[Decimal, TopicSegment(decimal_places=2)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=EventHandlerContext(event=event_dict,
                                           topic_pattern="test:topic:{value}",
                                           topic_delimiter=':')) as param:
        assert isinstance(param, Decimal)
        assert param == Decimal('123.45')


@pytest.mark.asyncio
async def test_decimal_validation_failure(event_dict):
    event_dict.topic = 'test:topic:123.45'

    def func(value: Annotated[Decimal, TopicSegment(decimal_places=1)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=EventHandlerContext(event=event_dict,
                                    topic_pattern="test:topic:{value}",
                                    topic_delimiter=':')
            )
