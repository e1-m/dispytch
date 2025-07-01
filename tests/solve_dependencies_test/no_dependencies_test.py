import pytest

from src.di.solv.solver import solve_dependencies


@pytest.mark.asyncio
async def test_empty_function():
    """Test function with no dependencies."""

    def empty_func():
        pass

    async with solve_dependencies(empty_func) as deps:
        assert deps == {}


@pytest.mark.asyncio
async def test_function_with_no_dependencies():
    """Test function with regular parameters but no dependencies."""

    def regular_func(a: int, b: str = "default"):
        pass

    async with solve_dependencies(regular_func) as deps:
        assert deps == {}
