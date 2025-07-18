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


@pytest.fixture
def func_annotated_instance():
    def func(value: Annotated[int, TopicSegment()]):
        pass

    return func


@pytest.fixture
def func_annotated_class():
    def func(value: Annotated[int, TopicSegment]):
        pass

    return func


@pytest.fixture
def func_default():
    def func(value: int = TopicSegment()):
        pass

    return func


@pytest.fixture
def func(request):
    return request.getfixturevalue(request.param)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "func",
    [
        pytest.param("func_annotated_instance", id="Annotated with an instance"),
        pytest.param("func_annotated_class", id="Annotated with a class"),
        pytest.param("func_default", id="Set as default")
    ],
    indirect=True
)
async def test_segment_match(event_dict, func):
    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=EventHandlerContext(event=event_dict,
                                           topic_pattern="test:topic:{value}",
                                           topic_delimiter=':')) as param:
        assert isinstance(param, int)
        assert param == 123
