from contextlib import asynccontextmanager

import pytest

from src.di.solv.solver import solve_dependencies
from src.di.dependency import Dependency


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

    async with solve_dependencies(target_func) as deps:
        assert deps["resource"] == "resource"
        assert not cleanup_called

    assert cleanup_called
