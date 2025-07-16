from typing import Annotated

from pydantic import BaseModel

from dispytch.di.event import Event
from dispytch.di.extractor import extract_dependencies
from dispytch.di.dependency import Dependency


class EventBody(BaseModel):
    name: str
    value: int


def test_mixed_parameters():
    """Test function with mix of regular params, dependencies, and annotated."""
    dep1 = Dependency(lambda: "test1")
    dep2 = Dependency(lambda: "test2")

    def mixed_func(
            annotated_param: Annotated[str, dep1],
            regular_param: int,
            dep_param=dep2,
            another_regular=None,
    ):
        pass

    result = extract_dependencies(mixed_func)

    assert len(result) == 2
    assert result["annotated_param"] == dep1
    assert result["dep_param"] == dep2


def test_complex_signature():
    """Test complex function signature with various parameter types."""
    dep1 = Dependency(lambda: "test2")
    dep2 = Dependency(lambda: "test1")

    def complex_func(
            *args,
            required_param: str,
            optional_param: int = 42,
            dep_param=dep1,
            annotated_dep: Annotated[list, "doc", dep2],
            **kwargs
    ):
        pass

    result = extract_dependencies(complex_func)

    assert len(result) == 2
    assert result["dep_param"] == dep1
    assert result["annotated_dep"] == dep2


def test_mixed_event_and_regular_params():
    def func_with_mixed_params(
            event_param: Event[EventBody],
            regular_param: int,
            another_param: str = "default",
            dep_param=Dependency(lambda: "fake_dependency"),
    ):
        pass

    result = extract_dependencies(func_with_mixed_params)

    assert len(result) == 2
    assert "event_param" in result
    assert "dep_param" in result

    assert "regular_param" not in result
    assert "another_param" not in result
