import pytest
from pydantic import BaseModel
from typing import Annotated

from dispytch.di.solver import DIResolver
from dispytch.di.context import DIContext
from dispytch.di.event import Event
from dispytch.di.subscription_param import SubscriptionParam
from dispytch.di.dependency import Dependency


class MyBody(BaseModel):
    name: str
    age: int


def some_user_dep():
    return "user_val"


@pytest.mark.asyncio
async def test_resolve_event_dependency():
    ctx = DIContext(
        event={"id": "123", "timestamp": 1000, "body": {"name": "John", "age": 30}},
        subscription_pattern=("user", "{id}"),
        actual_event_route=("user", "123")
    )
    resolver = DIResolver(ctx)

    async def my_handler(event: Event[MyBody]):
        pass

    async with resolver.resolve_internal_only(my_handler) as deps:
        assert "event" in deps
        event = deps["event"]
        assert isinstance(event, Event)
        assert isinstance(event.body, MyBody)
        assert event.body.name == "John"
        assert event.body.age == 30
        assert event.id == "123"
        assert event.timestamp == 1000


@pytest.mark.asyncio
async def test_resolve_subscription_param():
    ctx = DIContext(
        event={"id": "123", "timestamp": 1000, "body": {}},
        subscription_pattern=("user", "{user_id}", "action", "{action_id}"),
        actual_event_route=("user", "456", "action", "789")
    )
    resolver = DIResolver(ctx)

    async def my_handler(user_id: Annotated[int, SubscriptionParam()], action_id: int = SubscriptionParam()):
        pass

    async with resolver.resolve_internal_only(my_handler) as deps:
        assert deps["user_id"] == 456
        assert deps["action_id"] == 789


@pytest.mark.asyncio
async def test_ignores_user_defined_dependencies():
    ctx = DIContext(
        event={"id": "123", "timestamp": 1000, "body": {"name": "John", "age": 30}},
        subscription_pattern=(),
        actual_event_route=()
    )
    resolver = DIResolver(ctx)

    async def my_handler(event: Event[MyBody], user_val: str = Dependency(some_user_dep)):
        pass

    async with resolver.resolve_internal_only(my_handler) as deps:
        assert "event" in deps
        assert "user_val" not in deps


@pytest.mark.asyncio
async def test_mixed_internal_dependencies():
    ctx = DIContext(
        event={"id": "123", "timestamp": 1000, "body": {"name": "John", "age": 30}},
        subscription_pattern=("org", "{org_id}"),
        actual_event_route=("org", "my-org")
    )
    resolver = DIResolver(ctx)

    async def my_handler(event: Event[MyBody], org_id: str = SubscriptionParam()):
        pass

    async with resolver.resolve_internal_only(my_handler) as deps:
        assert deps["org_id"] == "my-org"
        assert deps["event"].body.name == "John"


@pytest.mark.asyncio
async def test_resolve_generic_event():
    ctx = DIContext(
        event={"id": "123", "timestamp": 1000, "body": {"any": "data"}},
        subscription_pattern=(),
        actual_event_route=()
    )
    resolver = DIResolver(ctx)

    async def my_handler(event: Event):
        pass

    async with resolver.resolve_internal_only(my_handler) as deps:
        assert deps["event"].body == {"any": "data"}


@pytest.mark.asyncio
async def test_subscription_param_missing_in_pattern():
    ctx = DIContext(
        event={"id": "123", "timestamp": 1000, "body": {}},
        subscription_pattern=("user", "{id}"),
        actual_event_route=("user", "123")
    )
    resolver = DIResolver(ctx)

    async def my_handler(missing_id: int = SubscriptionParam()):
        pass

    with pytest.raises(ValueError, match="no segment with such name was found in topic pattern"):
        async with resolver.resolve_internal_only(my_handler):
            pass


@pytest.mark.asyncio
async def test_subscription_param_validation_error():
    ctx = DIContext(
        event={"id": "123", "timestamp": 1000, "body": {}},
        subscription_pattern=("user", "{user_id}"),
        actual_event_route=("user", "not-an-int")
    )
    resolver = DIResolver(ctx)

    async def my_handler(user_id: int = SubscriptionParam()):
        pass

    with pytest.raises(ValueError, match="does not match the expected type constrains"):
        async with resolver.resolve_internal_only(my_handler):
            pass


@pytest.mark.asyncio
async def test_resolve_internal_only_same_dependency_twice():
    ctx = DIContext(
        event={"id": "123", "timestamp": 1000, "body": {"data": "test"}},
        subscription_pattern=(),
        actual_event_route=()
    )
    resolver = DIResolver(ctx)

    async def my_handler(event1: Event, event2: Event):
        pass

    async with resolver.resolve_internal_only(my_handler) as deps:
        assert "event1" in deps
        assert "event2" in deps
        assert deps["event1"].id == "123"
        assert deps["event2"].id == "123"

        assert deps["event1"] is not deps["event2"]
