from typing import Annotated

import pytest
from pydantic import BaseModel

from src.di.dependency import Dependency
from src.di.models import Event, EventHandlerContext
from src.di.solv.solver import solve_dependencies


@pytest.fixture
def event_dict():
    return {
        'topic': 'test-topic',
        'type': 'test-type',
        'body': {
            'name': 'test',
            'value': 42
        }
    }


@pytest.fixture
def handler_context(event_dict):
    return EventHandlerContext(event=event_dict)


class EventBody(BaseModel):
    name: str
    value: int


@pytest.mark.asyncio
async def test_single_event_dependency(handler_context):
    """Test function with a single event as a dependency."""

    def target_func(
            event: Event[EventBody],
    ):
        pass

    async with solve_dependencies(target_func, handler_context) as deps:
        assert len(deps) == 1

        dep = deps["event"]
        assert isinstance(dep, Event)
        assert dep.topic == handler_context.event['topic']
        assert dep.type == handler_context.event['type']
        assert isinstance(dep.body, EventBody)
        assert dep.body.name == handler_context.event['body']['name']
        assert dep.body.value == handler_context.event['body']['value']


@pytest.mark.asyncio
async def test_nested_event_dependency(handler_context):
    """Test function with a single event as a dependency of another dependency."""

    def get_value(event: Event[EventBody]):
        return event.body.value + 1

    default_dep = Dependency(get_value)

    def target_func(
            dep=default_dep,
    ):
        pass

    async with solve_dependencies(target_func, handler_context) as deps:
        assert len(deps) == 1
        assert deps["dep"] == handler_context.event['body']['value'] + 1


@pytest.mark.asyncio
async def test_various_body_models(handler_context):
    class Value(BaseModel):
        value: int

    class Name(BaseModel):
        name: str

    def get_value(event: Event[Value]):
        return event.body.value + 1

    def get_name(event: Event[Name]):
        return event.body.name

    value_dep = Annotated[int, Dependency(get_value)]
    name_dep = Annotated[str, Dependency(get_name)]

    def get_value_and_name(value: value_dep, name: name_dep):
        return f"{name} {value}"

    def target_func(
            value: value_dep,
            name: name_dep,
            value_and_name: Annotated[str, Dependency(get_value_and_name)],
    ):
        pass

    async with solve_dependencies(target_func, handler_context) as deps:
        assert len(deps) == 3
        name = handler_context.event['body']['name']
        value = handler_context.event['body']['value'] + 1

        assert deps["value"] == value
        assert deps["name"] == name
        assert deps["value_and_name"] == f"{name} {value}"


@pytest.mark.asyncio
async def test_dependency_mixed_with_event(handler_context):
    class Value(BaseModel):
        value: int

    def get_value(event: Event[Value]):
        return event.body.value + 1

    value_dep = Annotated[int, Dependency(get_value)]

    def get_multiplied_value(val: value_dep):
        return val * 2

    def get_service_name():
        return "test_service"

    def target_func(
            multiplied_value: Annotated[int, Dependency(get_multiplied_value)],
            service: Annotated[str, Dependency(get_service_name)],
    ):
        pass

    async with solve_dependencies(target_func, handler_context) as deps:
        assert len(deps) == 2

        value = handler_context.event['body']['value'] + 1

        assert deps["multiplied_value"] == value * 2
        assert deps["service"] == "test_service"
