import inspect
from typing import Annotated

from src.di.solv import _get_dependencies as get_dependencies  # noqa
from src.di.dependency import Dependency


def test_empty_signature():
    """Test function with no parameters."""

    def empty_func():
        pass

    sig = inspect.signature(empty_func)
    result = get_dependencies(sig)

    assert result == {}


def test_no_dependencies():
    """Test function with regular parameters but no dependencies."""

    def regular_func(a: int, b: str, c=None, d=1):
        pass

    sig = inspect.signature(regular_func)
    result = get_dependencies(sig)

    assert result == {}


def test_dependency_as_default_value():
    """Test parameter with Dependency as default value."""
    dep = Dependency(lambda: "test")

    def func_with_dep_default(service=dep):
        pass

    sig = inspect.signature(func_with_dep_default)
    result = get_dependencies(sig)

    assert len(result) == 1
    assert "service" in result
    assert result["service"] == dep


def test_multiple_dependencies_as_defaults():
    """Test multiple parameters with Dependencies as default values."""
    dep1 = Dependency(lambda: "test1")
    dep2 = Dependency(lambda: "test2")

    def func_with_multiple_deps(service1=dep1, service2=dep2):
        pass

    sig = inspect.signature(func_with_multiple_deps)
    result = get_dependencies(sig)

    assert len(result) == 2
    assert result["service1"] == dep1
    assert result["service2"] == dep2


def test_annotated_dependency():
    """Test parameter with Annotated type containing Dependency."""
    dep = Dependency(lambda: "test")

    def func_with_annotated(service: Annotated[str, dep]):
        pass

    sig = inspect.signature(func_with_annotated)
    result = get_dependencies(sig)

    assert len(result) == 1
    assert "service" in result
    assert result["service"] == dep


def test_annotated_multiple_metadata_with_dependency():
    """Test Annotated with multiple metadata items including Dependency."""
    dep = Dependency(lambda: "test")
    other_meta = "some_other_metadata"

    def func_with_meta(service: Annotated[int, other_meta, dep, "more_meta"]):
        pass

    sig = inspect.signature(func_with_meta)
    result = get_dependencies(sig)

    assert len(result) == 1
    assert result["service"] == dep


def test_annotated_no_dependency_in_metadata():
    """Test Annotated with metadata but no Dependency objects."""

    def func_with_meta_no_dep(service: Annotated[str, "metadata", 42]):
        pass

    sig = inspect.signature(func_with_meta_no_dep)
    result = get_dependencies(sig)

    assert result == {}


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


def test_dependency_default_takes_precedence_over_annotation():
    """Test that default Dependency takes precedence over annotated."""
    default_dep = Dependency(lambda: "test1")
    annotated_dep = Dependency(lambda: "test2")

    def func_with_both(param: Annotated[str, annotated_dep] = default_dep):
        pass

    sig = inspect.signature(func_with_both)
    result = get_dependencies(sig)

    # Should use the default dependency, not the annotated one
    assert len(result) == 1
    assert result["param"] == default_dep


def test_annotated_first_dependency_wins():
    """Test that first Dependency in Annotated metadata is used."""
    dep1 = Dependency(lambda: "test1")
    dep2 = Dependency(lambda: "test2")

    def func_with_multiple_deps_in_annotation(
            param: Annotated[str, dep1, dep2]
    ):
        pass

    sig = inspect.signature(func_with_multiple_deps_in_annotation)
    result = get_dependencies(sig)

    assert len(result) == 1
    assert result["param"] == dep1  # First dependency should win


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


###

def test_edge_case_none_annotation():
    """Test parameter with None annotation."""
    dep = Dependency(lambda: "test")

    def func_with_none_annotation(param: None = dep):
        pass

    sig = inspect.signature(func_with_none_annotation)
    result = get_dependencies(sig)

    assert len(result) == 1
    assert result["param"] == dep


def test_annotated_with_none_base_type():
    """Test Annotated with None as base type."""
    dep = Dependency(lambda: "test")

    def func_with_none_base(param: Annotated[None, dep]):
        pass

    sig = inspect.signature(func_with_none_base)
    result = get_dependencies(sig)

    assert len(result) == 1
    assert result["param"] == dep
