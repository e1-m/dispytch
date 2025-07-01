from typing import Annotated

import pytest

from dispytch.di.solver import solve_dependencies
from dispytch.di.dependency import Dependency


@pytest.mark.asyncio
async def test_single_dependency():
    """Test function with a single dependency."""

    def create_default_service():
        return "default_service"

    default_dep = Dependency(create_default_service)

    def target_func(
            default_svc=default_dep,
    ):
        pass

    async with solve_dependencies(target_func) as deps:
        assert len(deps) == 1
        assert deps["default_svc"] == "default_service"


@pytest.mark.asyncio
async def test_multiple_dependencies():
    """Test function with multiple dependencies."""

    def create_default_service():
        return "default_service"

    def create_annotated_service():
        return "annotated_service"

    default_dep = Dependency(create_default_service)
    annotated_dep = Dependency(create_annotated_service)

    def target_func(
            default_svc=default_dep,
            annotated_svc: Annotated[str, annotated_dep] = None
    ):
        pass

    async with solve_dependencies(target_func) as deps:
        assert len(deps) == 2
        assert deps["default_svc"] == "default_service"
        assert deps["annotated_svc"] == "annotated_service"


@pytest.mark.asyncio
async def test_nested_dependencies():
    """Test dependencies that have their own dependencies."""

    def create_config():
        return {"host": "localhost"}

    def create_db(config=Dependency(create_config)):
        return f"db_connected_to_{config['host']}"

    db_dep = Dependency(create_db)

    def target_func(database=db_dep):
        pass

    async with solve_dependencies(target_func) as deps:
        assert deps["database"] == "db_connected_to_localhost"


@pytest.mark.asyncio
async def test_deep_dependency_chain():
    """Test a deep chain of dependencies."""

    def create_level1():
        return "level1"

    def create_level2(dep1=Dependency(create_level1)):
        return f"level2({dep1})"

    def create_level3(dep2=Dependency(create_level2)):
        return f"level3({dep2})"

    dep = Dependency(create_level3)

    def target_func(service=dep):
        pass

    async with solve_dependencies(target_func) as deps:
        assert deps["service"] == "level3(level2(level1))"


@pytest.mark.asyncio
async def test_deeply_nested_unbalanced_dependencied():
    """Test a deep, unbalanced chain of dependencies."""

    def create_level1():
        return "level1"

    def create_level2(dep1=Dependency(create_level1)):
        return f"level2({dep1})"

    def create_level3_first_sibling(dep2=Dependency(create_level2)):
        return f"level3_first_sibling({dep2})"

    def create_level3_second_sibling():
        return f"level3_second_sibling"

    def create_level4(dep3=Dependency(create_level3_first_sibling), dep4=Dependency(create_level3_second_sibling)):
        return f"level4({dep3} + {dep4})"

    dep = Dependency(create_level4)

    def target_func(service=dep):
        pass

    async with solve_dependencies(target_func) as deps:
        assert deps["service"] == "level4(level3_first_sibling(level2(level1)) + level3_second_sibling)"
