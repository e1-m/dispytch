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
        'topic': 'test.topic.user.123',
        'type': 'test-type',
        'body': {
            'name': 'test',
            'value': 42
        },
        'timestamp': 100
    })


@pytest.fixture
def func_annotated_class_and_annotated_instance():
    def func(id: Annotated[int, TopicSegment], who: Annotated[str, TopicSegment()]):
        pass

    return func


@pytest.fixture
def func_annotated_and_default():
    def func(who: Annotated[str, TopicSegment()], id: int = TopicSegment()):
        pass

    return func


@pytest.fixture
def func(request):
    return request.getfixturevalue(request.param)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "func",
    [
        pytest.param("func_annotated_class_and_annotated_instance"),
        pytest.param("func_annotated_and_default"),
    ],
    indirect=True
)
async def test_multiple_segments_match(event_dict, func):
    result = extract_dependencies(func)

    assert len(result) == 2

    id_dep = result["id"]
    who_dep = result["who"]
    assert isinstance(id_dep, Dependency)
    assert isinstance(who_dep, Dependency)

    async with id_dep(ctx=EventHandlerContext(event=event_dict,
                                              topic_pattern="test.topic.{who}.{id}",
                                              topic_delimiter='.')) as param:
        assert isinstance(param, int)
        assert param == 123

    async with who_dep(ctx=EventHandlerContext(event=event_dict,
                                               topic_pattern="test.topic.{who}.{id}",
                                               topic_delimiter='.')) as param:
        assert isinstance(param, str)
        assert param == "user"


@pytest.mark.asyncio
async def test_multiple_args_depend_on_the_same_segment(event_dict):
    def func(who: Annotated[str, TopicSegment()], who_second: Annotated[str, TopicSegment(alias="who")]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 2

    who_dep = result["who"]
    who_second_dep = result["who_second"]
    assert isinstance(who_second_dep, Dependency)
    assert isinstance(who_dep, Dependency)

    async with who_second_dep(ctx=EventHandlerContext(event=event_dict,
                                                      topic_pattern="test.topic.{who}.{id}",
                                                      topic_delimiter='.')) as param:
        assert isinstance(param, str)
        assert param == "user"

    async with who_dep(ctx=EventHandlerContext(event=event_dict,
                                               topic_pattern="test.topic.{who}.{id}",
                                               topic_delimiter='.')) as param:
        assert isinstance(param, str)
        assert param == "user"
