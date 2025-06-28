from contextlib import asynccontextmanager
from typing import Annotated

import pytest

from src.di.exc import CyclicDependencyError, InvalidGeneratorError
from src.di.solv import get_solved_dependencies
from src.di.dependency import Dependency


@pytest.mark.asyncio
async def test_empty_function():
    """Test function with no dependencies."""

    def empty_func():
        pass

    async with get_solved_dependencies(empty_func) as deps:
        assert deps == {}


@pytest.mark.asyncio
async def test_function_with_no_dependencies():
    """Test function with regular parameters but no dependencies."""

    def regular_func(a: int, b: str = "default"):
        pass

    async with get_solved_dependencies(regular_func) as deps:
        assert deps == {}


@pytest.mark.asyncio
async def test_simple_sync_dependency():
    """Test a single synchronous dependency."""

    def create_service():
        return "sync_service"

    dep = Dependency(create_service)

    def target_func(service=dep):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert len(deps) == 1
        assert "service" in deps
        assert deps["service"] == "sync_service"


@pytest.mark.asyncio
async def test_simple_async_dependency():
    """Test a single asynchronous dependency."""

    async def create_async_service():
        return "async_service"

    dep = Dependency(create_async_service)

    def target_func(service=dep):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert len(deps) == 1
        assert deps["service"] == "async_service"


@pytest.mark.asyncio
async def test_async_context_manager_dependency():
    """Test dependency that returns an async context manager."""

    @asynccontextmanager
    async def create_cm_service():
        yield "cm_service"

    dep = Dependency(create_cm_service)

    def target_func(service=dep):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert deps["service"] == "cm_service"


@pytest.mark.asyncio
async def test_async_generator_dependency():
    """Test dependency that returns an async generator."""

    async def create_gen_service():
        yield "gen_service"

    dep = Dependency(create_gen_service)

    def target_func(service=dep):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert deps["service"] == "gen_service"


@pytest.mark.asyncio
async def test_multiple_dependencies():
    """Test function with multiple dependencies."""

    def create_db():
        return "database"

    def create_cache():
        return "cache"

    db_dep = Dependency(create_db)
    cache_dep = Dependency(create_cache)

    def target_func(db=db_dep, cache=cache_dep):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert len(deps) == 2
        assert deps["db"] == "database"
        assert deps["cache"] == "cache"


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

    async with get_solved_dependencies(target_func) as deps:
        assert deps["database"] == "db_connected_to_localhost"


@pytest.mark.asyncio
async def test_dependency_caching_within_different_resolutions():
    """Test that dependencies are not cached when using use_cache=True in different contexts."""
    call_count = 0

    def create_expensive_service():
        nonlocal call_count
        call_count += 1
        return f"service_{call_count}"

    dep = Dependency(create_expensive_service, use_cache=True)

    def func1(service=dep):
        pass

    def func2(service=dep):
        pass

    # First call
    async with get_solved_dependencies(func1) as deps1:
        assert "service_1" == deps1["service"]

    # Second call should not use cached value
    async with get_solved_dependencies(func2) as deps2:
        assert "service_2" == deps2["service"]

    assert call_count == 2  # Called twice because different contexts


@pytest.mark.asyncio
async def test_dependency_caching_within_same_resolution():
    """Test caching within the same dependency resolution context."""
    call_count = 0

    def create_shared_service():
        nonlocal call_count
        call_count += 1
        return f"shared_{call_count}"

    shared_dep = Dependency(create_shared_service, use_cache=True)

    def create_service1(shared=shared_dep):
        return f"service1_with_{shared}"

    def create_service2(shared=shared_dep):
        return f"service2_with_{shared}"

    dep1 = Dependency(create_service1)
    dep2 = Dependency(create_service2)

    def target_func(s1=dep1, s2=dep2):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert call_count == 1
        assert "service1_with_shared_1" == deps["s1"]
        assert "service2_with_shared_1" == deps["s2"]


@pytest.mark.asyncio
async def test_dependency_caching_disabled():
    """Test that caching can be disabled."""
    call_count = 0

    def create_service():
        nonlocal call_count
        call_count += 1
        return f"service_{call_count}"

    dep = Dependency(create_service, use_cache=False)

    def create_consumer1(service=dep):
        return f"consumer1_{service}"

    def create_consumer2(service=dep):
        return f"consumer2_{service}"

    dep1 = Dependency(create_consumer1)
    dep2 = Dependency(create_consumer2)

    def target_func(c1=dep1, c2=dep2):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert call_count == 2
        assert "consumer1_service_1" in deps["c1"]
        assert "consumer2_service_2" in deps["c2"]


@pytest.mark.asyncio
async def test_cyclic_dependency_detection():
    """Test that cyclic dependencies are detected and raise an error."""

    def create_a(b=None):
        return "service_a"

    def create_b(a=None):
        return "service_b"

    # Create cyclic dependencies
    dep_a = Dependency(create_a)
    dep_b = Dependency(create_b)

    # Manually setting up the cycle
    create_a.__defaults__ = (dep_b,)
    create_b.__defaults__ = (dep_a,)

    def target_func(service=dep_a):
        pass

    with pytest.raises(CyclicDependencyError, match="Dependency cycle detected"):
        async with get_solved_dependencies(target_func) as deps:
            pass


@pytest.mark.asyncio
async def test_annotated_dependencies():
    """Test dependencies specified through Annotated types."""

    def create_service():
        return "annotated_service"

    dep = Dependency(create_service)

    def target_func(service: Annotated[str, dep]):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert deps["service"] == "annotated_service"


@pytest.mark.asyncio
async def test_mixed_dependency_sources():
    """Test mix of default and annotated dependencies."""

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

    async with get_solved_dependencies(target_func) as deps:
        assert len(deps) == 2
        assert deps["default_svc"] == "default_service"
        assert deps["annotated_svc"] == "annotated_service"


@pytest.mark.asyncio
async def test_dependency_with_async_context_manager_cleanup():
    """Test that async context managers are properly cleaned up."""
    cleanup_called = False

    @asynccontextmanager
    async def create_resource():
        nonlocal cleanup_called
        try:
            yield "resource"
        finally:
            cleanup_called = True

    dep = Dependency(create_resource)

    def target_func(resource=dep):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert deps["resource"] == "resource"
        assert not cleanup_called

    assert cleanup_called


@pytest.mark.asyncio
async def test_async_generator_validation():
    """Test validation of async generators."""

    async def empty_generator():
        return
        yield  # noqa

    async def multi_yield_generator():
        yield "first"
        yield "second"

    empty_dep = Dependency(empty_generator)
    multi_dep = Dependency(multi_yield_generator)

    def target_func1(service=empty_dep):
        pass

    def target_func2(service=multi_dep):
        pass

    # Empty generator should raise InvalidGeneratorError
    with pytest.raises(InvalidGeneratorError, match="didn't yield any value"):
        async with get_solved_dependencies(target_func1) as deps:
            pass

    # Multiple yield generator should raise InvalidGeneratorError
    with pytest.raises(InvalidGeneratorError, match="yielded more than one value"):
        async with get_solved_dependencies(target_func2) as deps:
            pass


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

    async with get_solved_dependencies(target_func) as deps:
        assert deps["service"] == "level3(level2(level1))"


@pytest.mark.asyncio
async def test_dependency_hash_consistency():
    """Test that dependency hashing works correctly for caching."""

    def create_service():
        return "service"

    dep1 = Dependency(create_service)
    dep2 = Dependency(create_service)

    # Same function should have same hash
    assert hash(dep1) == hash(dep2)

    def create_other_service():
        return "other"

    dep3 = Dependency(create_other_service)

    # Different function should have different hash
    assert hash(dep1) != hash(dep3)


@pytest.mark.asyncio
async def test_exception_in_dependency_creation():
    """Test error handling when dependency creation fails."""

    def failing_dependency():
        raise ValueError("Dependency creation failed")

    dep = Dependency(failing_dependency)

    def target_func(service=dep):
        pass

    with pytest.raises(ValueError, match="Dependency creation failed"):
        async with get_solved_dependencies(target_func) as deps:
            pass


@pytest.mark.asyncio
async def test_exception_in_async_dependency_creation():
    """Test error handling when async dependency creation fails."""

    async def failing_async_dependency():
        raise RuntimeError("Async dependency failed")

    dep = Dependency(failing_async_dependency)

    def target_func(service=dep):
        pass

    with pytest.raises(RuntimeError, match="Async dependency failed"):
        async with get_solved_dependencies(target_func) as deps:
            pass


@pytest.mark.asyncio
async def test_multiple_usage_of_same_context_manager():
    """Test that the same dependency can be resolved multiple times in different contexts."""
    creation_count = 0

    @asynccontextmanager
    async def create_resource():
        nonlocal creation_count
        creation_count += 1
        try:
            yield f"resource_{creation_count}"
        finally:
            pass

    dep = Dependency(create_resource)

    def target_func(resource=dep):
        pass

    # First usage
    async with get_solved_dependencies(target_func) as deps1:
        result1 = deps1["resource"]

    # Second usage
    async with get_solved_dependencies(target_func) as deps2:
        result2 = deps2["resource"]

    # Each call should create a new instance
    assert result1 == "resource_1"
    assert result2 == "resource_2"
    assert creation_count == 2


@pytest.mark.asyncio
async def test_parameter_name_preservation():
    """Test that parameter names are preserved in the result dictionary."""

    def create_database():
        return "db"

    def create_cache_service():
        return "cache"

    db_dep = Dependency(create_database)
    cache_dep = Dependency(create_cache_service)

    def target_func(
            database_connection=db_dep,
            cache_service=cache_dep
    ):
        pass

    async with get_solved_dependencies(target_func) as deps:
        assert "database_connection" in deps
        assert "cache_service" in deps
        assert deps["database_connection"] == "db"
        assert deps["cache_service"] == "cache"
