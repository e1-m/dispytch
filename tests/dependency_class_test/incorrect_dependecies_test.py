import pytest

from dispytch.di.dependency import Dependency
from dispytch.di.exc import InvalidGeneratorError


@pytest.mark.asyncio
async def test_async_generator_multiple_yield():
    """Test dependency with async generator with multiple yield."""

    async def create_async_gen_service():
        yield "async_gen_service"
        yield "something else"

    dep = Dependency(create_async_gen_service)

    with pytest.raises(InvalidGeneratorError):
        async with dep() as dependency:
            pass


@pytest.mark.asyncio
async def test_sync_generator_multiple_yield():
    """Test dependency with sync generator with multiple yield."""

    def create_gen_service():
        yield "gen_service"
        yield "something else"

    dep = Dependency(create_gen_service)

    with pytest.raises(InvalidGeneratorError):
        async with dep() as dependency:
            pass


@pytest.mark.asyncio
async def test_not_yielding_async_generator():
    """Test dependency with a not yielding async generator."""

    async def empty_generator():
        return
        yield  # noqa

    empty_dep = Dependency(empty_generator)

    def target_func1(service=empty_dep):
        pass

    with pytest.raises(InvalidGeneratorError, match="didn't yield any value"):
        async with empty_dep() as dependency:
            pass


@pytest.mark.asyncio
async def test_not_yielding_sync_generator():
    """Test dependency with a not yielding sync generator."""

    def empty_generator():
        return
        yield  # noqa

    empty_dep = Dependency(empty_generator)

    def target_func1(service=empty_dep):
        pass

    with pytest.raises(InvalidGeneratorError, match="didn't yield any value"):
        async with empty_dep() as dependency:
            pass
