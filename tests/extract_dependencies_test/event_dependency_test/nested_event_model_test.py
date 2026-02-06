import uuid

import pytest
from pydantic import BaseModel

from dispytch.di.dependency import Dependency
from dispytch.di.context import DIContext
from dispytch.di.event import Event
from dispytch.di.extractor import extract_dependencies


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


@pytest.mark.asyncio
async def test_nested_event(event_dict):
    def func_with_event(event_param: Event[EventBody]):
        pass

    result = extract_dependencies(func_with_event)

    assert len(result) == 1

    dep = result["event_param"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=DIContext(
            event=event_dict,
            subscription_pattern=("topic",),
            actual_event_route=("topic",)
    )) as event:
        assert isinstance(event, EventBody)
        assert event.name == event_dict['name']
        assert event.value == event_dict['value']
        assert isinstance(event.metadata, Metadata)
        assert event.metadata.timestamp == event_dict['metadata']['timestamp']
        assert isinstance(event.metadata.sender, Sender)
        assert event.metadata.sender.name == event_dict['metadata']['sender']['name']
        assert event.metadata.sender.age == event_dict['metadata']['sender']['age']

        with pytest.raises(AttributeError):
            assert event.body.additional == 'extra data'
