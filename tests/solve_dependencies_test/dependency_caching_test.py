import pytest

from src.di.solv.solver import solve_dependencies
from src.di.dependency import Dependency


@pytest.mark.asyncio
async def test_dependency_caching_within_the_same_context():
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

    async with solve_dependencies(target_func) as deps:
        assert call_count == 1
        assert "service1_with_shared_1" == deps["s1"]
        assert "service2_with_shared_1" == deps["s2"]


@pytest.mark.asyncio
async def test_dependency_caching_within_different_contexts():
    """Test that dependencies are not cached when using use_cache=True in different contexts."""
    call_count = 0

    def create_expensive_service():
        nonlocal call_count
        call_count += 1
        return f"service_{call_count}"

    dep = Dependency(create_expensive_service, use_cache=True)

    def func1(service1=dep):
        pass

    def func2(service2=dep):
        pass

    # First call
    async with solve_dependencies(func1) as deps1:
        assert "service_1" == deps1["service1"]

    # Second call should not use cached value
    async with solve_dependencies(func2) as deps2:
        assert "service_2" == deps2["service2"]

    assert call_count == 2  # Called twice because different contexts


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dep1_use_cache,dep2_use_cache",
    [
        (True, False),
        (False, True),
        (False, False),
    ],
)
async def test_dependency_caching_disabled(dep1_use_cache, dep2_use_cache):
    """Test that caching can be disabled."""
    call_count = 0

    def create_service():
        nonlocal call_count
        call_count += 1
        return f"service_{call_count}"

    def create_consumer1(service=Dependency(create_service, use_cache=dep1_use_cache)):
        return f"consumer1_{service}"

    def create_consumer2(service=Dependency(create_service, use_cache=dep2_use_cache)):
        return f"consumer2_{service}"

    dep1 = Dependency(create_consumer1)
    dep2 = Dependency(create_consumer2)

    def target_func(c1=dep1, c2=dep2):
        pass

    async with solve_dependencies(target_func) as deps:
        assert call_count == 2
        assert "consumer1_service_1" in deps["c1"]
        assert "consumer2_service_2" in deps["c2"]


@pytest.mark.asyncio
async def test_dependency_caching_with_different_key_words():
    call_count = 0

    def create_shared_service():
        nonlocal call_count
        call_count += 1
        return f"shared_{call_count}"

    shared_dep = Dependency(create_shared_service, use_cache=True)

    def target_func(s1=shared_dep, s2=shared_dep):
        pass

    async with solve_dependencies(target_func) as deps:
        assert call_count == 1
        assert "shared_1" == deps["s1"]
        assert "shared_1" == deps["s2"]
