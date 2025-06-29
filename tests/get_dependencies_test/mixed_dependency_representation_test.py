import inspect
from typing import Annotated

from src.di.solv import _get_dependencies as get_dependencies  # noqa
from src.di.dependency import Dependency


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

    sig = inspect.signature(mixed_func)
    result = get_dependencies(sig)

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

    sig = inspect.signature(complex_func)
    result = get_dependencies(sig)

    assert len(result) == 2
    assert result["dep_param"] == dep1
    assert result["annotated_dep"] == dep2
