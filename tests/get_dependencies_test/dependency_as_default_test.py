from typing import Annotated

from src.di.solv.extractor import _get_user_defined_dependencies as get_dependencies
from src.di.dependency import Dependency


def test_dependency_as_default_value():
    """Test parameter with Dependency as default value."""
    dep = Dependency(lambda: "test")

    def func_with_dep_default(service=dep):
        pass

    result = get_dependencies(func_with_dep_default)

    assert len(result) == 1
    assert "service" in result
    assert result["service"] == dep


def test_multiple_dependencies_as_defaults():
    """Test multiple parameters with Dependencies as default values."""
    dep1 = Dependency(lambda: "test1")
    dep2 = Dependency(lambda: "test2")

    def func_with_multiple_deps(service1=dep1, service2=dep2):
        pass

    result = get_dependencies(func_with_multiple_deps)

    assert len(result) == 2
    assert result["service1"] == dep1
    assert result["service2"] == dep2


def test_dependency_default_takes_precedence_over_annotation():
    """Test that default Dependency takes precedence over annotated."""
    default_dep = Dependency(lambda: "test1")
    annotated_dep = Dependency(lambda: "test2")

    def func_with_both(param: Annotated[str, annotated_dep] = default_dep):
        pass

    result = get_dependencies(func_with_both)

    # Should use the default dependency, not the annotated one
    assert len(result) == 1
    assert result["param"] == default_dep
