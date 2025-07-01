import asyncio
from contextlib import asynccontextmanager, AsyncExitStack

import pytest

from src.di.solv.solver import solve_dependencies
from src.di.dependency import Dependency


@pytest.mark.asyncio
async def test_dependency_cleanup():
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

    async with solve_dependencies(target_func) as deps:
        assert deps["resource"] == "resource"
        assert not cleanup_called

    assert cleanup_called


@pytest.mark.asyncio
async def test_dependency_cleanup_in_concurrent_environment():
    """Test that async context managers are properly cleaned up in a concurrent environment."""
    cleanup_called_times = 0

    @asynccontextmanager
    async def create_resource():
        nonlocal cleanup_called_times
        try:
            yield "resource"
        finally:
            cleanup_called_times += 1

    dep = Dependency(create_resource)

    def target_func(resource=dep):
        pass

    number_of_tasks = 10
    async with AsyncExitStack() as stack:  # noqa
        tasks = [asyncio.create_task(
            stack.enter_async_context(
                solve_dependencies(target_func)
            )
        ) for _ in range(number_of_tasks)]

        await asyncio.gather(*tasks)

    assert cleanup_called_times == number_of_tasks
