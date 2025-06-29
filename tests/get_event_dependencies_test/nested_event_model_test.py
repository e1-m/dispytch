import pytest
from pydantic import BaseModel

from src.di.dependency import Dependency
from src.di.models import Event, EventHandlerContext
from src.di.solv import _get_event_requests_as_dependencies as get_event_dependencies  # noqa


class Sender(BaseModel):
    name: str
    age: int


class Metadata(BaseModel):
    timestamp: str
    sender: Sender


class EventBody(BaseModel):
    name: str
    value: int
    metadata: Metadata


@pytest.fixture
def event_dict():
    return {
        'topic': 'test-topic',
        'type': 'test-type',
        'body': {
            'name': 'test',
            'value': 42,
            'metadata': {
                'timestamp': '2023-01-01T00:00:00Z',
                'sender': {
                    'name': 'John Doe',
                    'age': 25
                }
            },
            'additional': 'extra data',
        }
    }


@pytest.mark.asyncio
async def test_nested_event(event_dict):
    def func_with_event(event_param: Event[EventBody]):
        pass

    result = get_event_dependencies(func_with_event, EventHandlerContext(event=event_dict))

    assert len(result) == 1

    dep = result["event_param"]
    assert isinstance(dep, Dependency)

    async with dep() as event:
        assert isinstance(event, Event)
        assert isinstance(event.body, EventBody)
        assert event.body.name == event_dict['body']['name']
        assert event.body.value == event_dict['body']['value']
        assert isinstance(event.body.metadata, Metadata)
        assert event.body.metadata.timestamp == event_dict['body']['metadata']['timestamp']
        assert isinstance(event.body.metadata.sender, Sender)
        assert event.body.metadata.sender.name == event_dict['body']['metadata']['sender']['name']
        assert event.body.metadata.sender.age == event_dict['body']['metadata']['sender']['age']

        with pytest.raises(AttributeError):
            assert event.body.additional == 'extra data'
