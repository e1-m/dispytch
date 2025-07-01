from contextlib import asynccontextmanager, contextmanager

import pytest

from dispytch.di.dependency import Dependency


@pytest.mark.asyncio
async def test_simple_sync_dependency():
    """Test dependency with a synchronous function."""

    def create_service():
        return "sync_service"

    dep = Dependency(create_service)

    async with dep() as dependency:
        assert dependency == "sync_service"


@pytest.mark.asyncio
async def test_simple_async_dependency():
    """Test dependency with an asynchronous function."""

    async def create_async_service():
        return "async_service"

    dep = Dependency(create_async_service)

    async with dep() as dependency:
        assert dependency == "async_service"


@pytest.mark.asyncio
async def test_async_generator_dependency():
    """Test dependency with an async generator."""
    cleanup_called = False

    async def create_async_gen_service():
        nonlocal cleanup_called
        yield "async_gen_service"
        cleanup_called = True

    dep = Dependency(create_async_gen_service)

    async with dep() as dependency:
        assert dependency == "async_gen_service"
        assert not cleanup_called
    assert cleanup_called


@pytest.mark.asyncio
async def test_sync_generator_dependency():
    """Test dependency with a sync generator."""
    cleanup_called = False

    def create_gen_service():
        nonlocal cleanup_called
        yield "gen_service"
        cleanup_called = True

    dep = Dependency(create_gen_service)

    async with dep() as dependency:
        assert dependency == "gen_service"
        assert not cleanup_called
    assert cleanup_called


@pytest.mark.asyncio
async def test_async_context_manager_dependency():
    """Test dependency with an async context manager"""
    cleanup_called = False

    @asynccontextmanager
    async def create_async_cm_service():
        nonlocal cleanup_called
        yield "async_cm_service"
        cleanup_called = True

    dep = Dependency(create_async_cm_service)

    async with dep() as dependency:
        assert dependency == "async_cm_service"
        assert not cleanup_called
    assert cleanup_called


@pytest.mark.asyncio
async def test_sync_context_manager_dependency():
    """Test dependency with a sync context manager."""
    cleanup_called = False

    @contextmanager
    def create_gen_service():
        nonlocal cleanup_called
        yield "cm_service"
        cleanup_called = True

    dep = Dependency(create_gen_service)

    async with dep() as dependency:
        assert dependency == "cm_service"
        assert not cleanup_called
    assert cleanup_called


@pytest.mark.asyncio
async def test_async_iterator_dependency():
    """Test dependency with an async iterator."""

    class AsyncIteratorService:
        def __init__(self):
            self.cleanup_called = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not hasattr(self, '_yielded'):
                self._yielded = True
                return "async_iter_service"
            else:
                self.cleanup_called = True
                raise StopAsyncIteration

    service_instance = AsyncIteratorService()

    def create_async_iter_service():
        return service_instance

    dep = Dependency(create_async_iter_service)

    async with dep() as dependency:
        assert dependency == "async_iter_service"
        assert not service_instance.cleanup_called

    assert service_instance.cleanup_called


@pytest.mark.asyncio
async def test_sync_iterator_dependency():
    """Test dependency with a sync iterator."""

    class SyncIteratorService:
        def __init__(self):
            self.cleanup_called = False

        def __iter__(self):
            return self

        def __next__(self):
            if not hasattr(self, '_yielded'):
                self._yielded = True
                return "iter_service"
            else:
                self.cleanup_called = True
                raise StopIteration

    service_instance = SyncIteratorService()

    def create_iter_service():
        return service_instance

    dep = Dependency(create_iter_service)

    async with dep() as dependency:
        assert dependency == "iter_service"
        assert not service_instance.cleanup_called

    assert service_instance.cleanup_called
