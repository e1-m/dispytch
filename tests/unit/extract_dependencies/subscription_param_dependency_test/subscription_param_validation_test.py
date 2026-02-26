from decimal import Decimal
from typing import Annotated, Literal

import pytest

from dispytch import Dependency
from dispytch.di.extractor import extract_dependencies
from dispytch.di.context import DIContext
from dispytch.di.subscription_param import SubscriptionParam


@pytest.fixture
def event_dict():
    return {
        'name': 'test',
        'value': 42
    }


@pytest.mark.asyncio
async def test_literal_validation_success(event_dict):
    def func(value: Annotated[Literal["test", "example", "123"], SubscriptionParam()]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=DIContext(event=event_dict,
                                 actual_event_route=tuple("test:topic:123".split(':')),
                                 subscription_pattern=tuple("test:topic:{value}".split(':'))
                                 )) as param:
        assert isinstance(param, str)
        assert param == "123"


@pytest.mark.asyncio
async def test_literal_validation_failure(event_dict):
    def func(value: Annotated[Literal["test", "example"], SubscriptionParam()]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=DIContext(event=event_dict,
                          actual_event_route=tuple("test:topic:123".split(':')),
                          subscription_pattern=tuple("test:topic:{value}".split(':'))
                          )
            )


@pytest.mark.asyncio
async def test_int_validation_success(event_dict):
    def func(value: Annotated[int, SubscriptionParam(le=125)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=DIContext(event=event_dict,
                                 actual_event_route=tuple("test:topic:123".split(':')),
                                 subscription_pattern=tuple("test:topic:{value}".split(':'))
                                 )) as param:
        assert isinstance(param, int)
        assert param == 123


@pytest.mark.asyncio
async def test_int_validation_failure(event_dict):
    def func(value: Annotated[int, SubscriptionParam(le=100)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=DIContext(event=event_dict,
                          actual_event_route=tuple("test:topic:123".split(':')),
                          subscription_pattern=tuple("test:topic:{value}".split(':'))
                          )
            )


@pytest.mark.asyncio
async def test_str_validation_success(event_dict):
    def func(value: Annotated[str, SubscriptionParam(min_length=1)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=DIContext(event=event_dict,
                                 actual_event_route=tuple("test:topic:123".split(':')),
                                 subscription_pattern=tuple("test:topic:{value}".split(':'))
                                 )) as param:
        assert isinstance(param, str)
        assert param == "123"


@pytest.mark.asyncio
async def test_str_validation_failure(event_dict):
    def func(value: Annotated[str, SubscriptionParam(min_length=10)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(ctx=DIContext(event=event_dict,
                          actual_event_route=tuple("test:topic:123".split(':')),
                          subscription_pattern=tuple("test:topic:{value}".split(':'))
                          ))


@pytest.mark.asyncio
async def test_str_validation_inappropriate_constrains(event_dict):
    def func(value: Annotated[str, SubscriptionParam(le=100)]):
        pass

    result = extract_dependencies(func)

    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(TypeError):
        dep(ctx=DIContext(event=event_dict,
                          actual_event_route=tuple("test:topic:123".split(':')),
                          subscription_pattern=tuple("test:topic:{value}".split(':'))
                          ))


@pytest.mark.asyncio
async def test_decimal_validation_success(event_dict):
    def func(value: Annotated[Decimal, SubscriptionParam(decimal_places=2)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    async with dep(ctx=DIContext(event=event_dict,
                                 actual_event_route=tuple("test:topic:123.45".split(':')),
                                 subscription_pattern=tuple("test:topic:{value}".split(':'))
                                 )) as param:
        assert isinstance(param, Decimal)
        assert param == Decimal('123.45')


@pytest.mark.asyncio
async def test_decimal_validation_failure(event_dict):
    def func(value: Annotated[Decimal, SubscriptionParam(decimal_places=1)]):
        pass

    result = extract_dependencies(func)
    assert len(result) == 1

    dep = result["value"]
    assert isinstance(dep, Dependency)

    with pytest.raises(ValueError):
        dep(
            ctx=DIContext(event=event_dict,
                          actual_event_route=tuple("test:topic:123.45".split(':')),
                          subscription_pattern=tuple("test:topic:{value}".split(':'))
                          )
        )
