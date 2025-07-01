import pytest

from src.di.exc import CyclicDependencyError
from src.di.solv.solver import solve_dependencies
from src.di.dependency import Dependency


@pytest.mark.asyncio
async def test_cyclic_dependency_detection():
    """Test that cyclic dependencies are detected and raise an error."""

    def create_a(b=None):
        return "service_a"

    def create_b(a=None):
        return "service_b"

    dep_a = Dependency(create_a)
    dep_b = Dependency(create_b)

    # Manually setting up the cycle
    create_a.__defaults__ = (dep_b,)
    create_b.__defaults__ = (dep_a,)

    def target_func(service=dep_a):
        pass

    with pytest.raises(CyclicDependencyError, match="Dependency cycle detected"):
        async with solve_dependencies(target_func) as deps:
            pass
