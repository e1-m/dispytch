import uuid
from typing import Annotated

import pytest

from dispytch import Dependency
from dispytch.di.extractor import extract_dependencies
from dispytch.di.context import DIContext
from dispytch.di.event import Event
from dispytch.di.subscription_param import SubscriptionParam


@pytest.fixture
def event_dict():
    return Event(**{
        'id': str(uuid.uuid4()),
        'body': {
            'name': 'test',
            'value': 42
        },
        'timestamp': 100
    })


@pytest.mark.asyncio
async def test_segment_mismatch(event_dict, ):
    def func(value: Annotated[int, SubscriptionParam()]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=DIContext(event=event_dict,
                          actual_event_route=tuple("test:topic:123".split(':')),
                          subscription_pattern=tuple("test:topic:{not_value}".split(':'))
                          ))


@pytest.mark.asyncio
async def test_segment_mismatch_same_name_in_static_topic(event_dict, ):
    def func(value: Annotated[int, SubscriptionParam()]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=DIContext(event=event_dict,
                          actual_event_route=tuple("test:topic:123".split(':')),
                          subscription_pattern=tuple("test:topic:value".split(':'))
                          ))


@pytest.mark.asyncio
async def test_segment_mismatch_different_delimiter(event_dict, ):
    def func(value: Annotated[int, SubscriptionParam()]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=DIContext(event=event_dict,
                          actual_event_route=tuple("test:topic:123".split('.')),
                          subscription_pattern=tuple("test:topic:{value}".split('.'))
                          ))
