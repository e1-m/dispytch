import uuid
from typing import Annotated

import pytest

from dispytch.di.extractor import extract_dependencies
from dispytch.di.context import EventHandlerContext
from dispytch.di.event import Event
from dispytch.di.dependency import Dependency
from dispytch.di.solver import solve_dependencies
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


@pytest.fixture
def func(request):
    def dep(value: int = TopicSegment()):
        return value + 1

    def func(val: Annotated[int, Dependency(dep)]):
        return val

    return func


@pytest.mark.asyncio
async def test_segment_match(event_dict, func):
    result = extract_dependencies(func)

    assert len(result) == 1

    async with solve_dependencies(func,
                                  ctx=EventHandlerContext(event=event_dict,
                                                          topic_pattern="test:topic:{value}",
                                                          topic_delimiter=':')) as deps:
        assert len(deps) == 1
        assert deps["val"] == 124
