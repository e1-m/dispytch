import asyncio

import pytest

from dispytch.di.dependency import Dependency
from dispytch.di.solver import solve_dependencies


@pytest.mark.asyncio
async def test_with_two_parallel_dependencies():
    async def create_first_service():
        await asyncio.sleep(0.1)
        return f"first_service"

    async def create_second_service():
        await asyncio.sleep(0.2)
        return f"second_service"

    dep1 = Dependency(create_first_service)
    dep2 = Dependency(create_second_service)

    def target_func(s1=dep1, s2=dep2):
        pass

    start_time = asyncio.get_event_loop().time()
    async with solve_dependencies(target_func) as deps:
        assert "first_service" == deps["s1"]
        assert "second_service" == deps["s2"]
        end_time = asyncio.get_event_loop().time()
        assert round(end_time - start_time, 1) == 0.2


@pytest.mark.asyncio
async def test_with_shared_dependency():
    async def create_shared_service():
        await asyncio.sleep(0.1)
        return f"shared_service"

    shared_dep = Dependency(create_shared_service)

    async def create_first_service(shared1=shared_dep):
        await asyncio.sleep(0.1)
        return f"first_service {shared1}"

    async def create_second_service(shared2=shared_dep):
        await asyncio.sleep(0.2)
        return f"second_service {shared2}"

    dep1 = Dependency(create_first_service)
    dep2 = Dependency(create_second_service)

    def target_func(s1=dep1, s2=dep2):
        pass

    start_time = asyncio.get_event_loop().time()
    async with solve_dependencies(target_func) as deps:
        assert "first_service shared_service" == deps["s1"]
        assert "second_service shared_service" == deps["s2"]
        end_time = asyncio.get_event_loop().time()
        assert round(end_time - start_time, 1) == 0.3


@pytest.mark.asyncio
async def test_with_shared_root_dependency():
    call_count = 0

    async def create_shared_service():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)
        return f"shared_{call_count}"

    shared_dep = Dependency(create_shared_service, use_cache=True)

    def target_func(s1=shared_dep, s2=shared_dep):
        pass

    start_time = asyncio.get_event_loop().time()
    async with solve_dependencies(target_func) as deps:
        end_time = asyncio.get_event_loop().time()
        assert round(end_time - start_time, 1) == 0.1  # 1 concurrent call
        assert call_count == 1
        assert "shared_1" == deps["s1"]
        assert "shared_1" == deps["s2"]


@pytest.mark.asyncio
async def test_with_shared_root_dependency_without_cache():
    call_count = 0

    async def create_shared_service():
        nonlocal call_count
        await asyncio.sleep(0.1)
        call_count += 1
        return f"shared_{call_count}"

    shared_dep = Dependency(create_shared_service, use_cache=False)

    def target_func(s1=shared_dep, s2=shared_dep):
        pass

    start_time = asyncio.get_event_loop().time()
    async with solve_dependencies(target_func) as deps:
        end_time = asyncio.get_event_loop().time()
        assert round(end_time - start_time, 1) == 0.1  # 2 concurrent calls
        assert call_count == 2
        assert "shared_1" == deps["s1"]
        assert "shared_2" == deps["s2"]
