import uuid
from typing import Annotated

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
async def test_segment_mismatch(event_dict, ):
    def func(value: Annotated[int, TopicSegment()]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=EventHandlerContext(event=event_dict,
                                    topic_pattern="test:topic:{not_value}",
                                    topic_delimiter=':'))


@pytest.mark.asyncio
async def test_segment_mismatch_same_name_in_static_topic(event_dict, ):
    def func(value: Annotated[int, TopicSegment()]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=EventHandlerContext(event=event_dict,
                                    topic_pattern="test:topic:value",
                                    topic_delimiter=':'))


@pytest.mark.asyncio
async def test_segment_mismatch_different(event_dict, ):
    def func(value: Annotated[int, TopicSegment()]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=EventHandlerContext(event=event_dict,
                                    topic_pattern="test:topic:{value}",
                                    topic_delimiter='.'))
