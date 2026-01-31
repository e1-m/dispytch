import uuid
from typing import Annotated

import pytest

from dispytch import Dependency
from dispytch.di.extractor import extract_dependencies
from dispytch.di.context import EventHandlerContext
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


@pytest.fixture
def alias():
    return "v"


@pytest.fixture
def func_with_alias(alias):
    def func(value: Annotated[int, SubscriptionParam(alias=alias)]):
        pass

    return func


@pytest.fixture
def func_with_validation_alias(alias):
    def func(value: int = SubscriptionParam(validation_alias=alias)):
        pass

    return func


@pytest.fixture
def func_with_validation_alias_and_general_alias(alias):
    def func(value: int = SubscriptionParam(validation_alias=alias, alias="something_else")):
        pass

    return func


@pytest.fixture
def func(request):
    return request.getfixturevalue(request.param)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "func",
    [
        pytest.param("func_with_alias", id="Aliased"),
        pytest.param("func_with_validation_alias", id="Aliased by validation alias"),
        pytest.param("func_with_validation_alias_and_general_alias", id="Validation alias takes precedence")
    ],
    indirect=True
)
async def test_aliased_segment_match(event_dict, func, alias):
    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(
            ctx=EventHandlerContext(
                event=event_dict,
                subscription_pattern=f"test:topic:{{{alias}}}",
                actual_event_route="test:topic:123",
                route_delimiter=':'
            )
    ) as param:
        assert isinstance(param, int)
        assert param == 123
