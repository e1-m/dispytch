import asyncio
import pytest
from dispytch.middleware.async_lock import AsyncLock
from dispytch.dispatcher.handler import EventHandlerContext


@pytest.fixture
def ctx():
    return EventHandlerContext(
        event={"data": "test"},
        subscription_pattern=("test",),
        actual_event_route=("test",)
    )


@pytest.mark.asyncio
async def test_async_lock_basic_locking(ctx):
    lock_middleware = AsyncLock(key_extractor=lambda c: c.event["data"], concurrency_limit=1)

    counter = 0

    async def call_next_with_counter(c):
        nonlocal counter
        counter += 1
        await asyncio.sleep(0.1)

    t1 = asyncio.create_task(lock_middleware.dispatch(ctx, call_next_with_counter))
    await asyncio.sleep(0.05)
    assert counter == 1

    t2 = asyncio.create_task(lock_middleware.dispatch(ctx, call_next_with_counter))
    await asyncio.sleep(0.02)
    assert counter == 1  # Still 1 because t2 is blocked

    await t1
    await asyncio.sleep(0.01)  # Give t2 a chance to enter
    assert counter == 2
    await t2


@pytest.mark.asyncio
async def test_async_lock_different_keys():
    lock_middleware = AsyncLock(key_extractor=lambda c: c.event["key"], concurrency_limit=1)

    counter = 0

    async def call_next(c):
        nonlocal counter
        counter += 1
        await asyncio.sleep(0.1)

    ctx1 = EventHandlerContext(event={"key": "key1"}, subscription_pattern=(), actual_event_route=())
    ctx2 = EventHandlerContext(event={"key": "key2"}, subscription_pattern=(), actual_event_route=())

    # Start two tasks for different keys
    t1 = asyncio.create_task(lock_middleware.dispatch(ctx1, call_next))
    t2 = asyncio.create_task(lock_middleware.dispatch(ctx2, call_next))

    # Both should start immediately because they have different keys
    await asyncio.sleep(0.05)
    assert counter == 2

    await t1
    await t2


@pytest.mark.asyncio
async def test_async_lock_concurrency_limit(ctx):
    lock_middleware = AsyncLock(key_extractor=lambda c: c.event["data"], concurrency_limit=2)

    counter = 0

    async def call_next(c):
        nonlocal counter
        counter += 1
        await asyncio.sleep(0.1)

    t1 = asyncio.create_task(lock_middleware.dispatch(ctx, call_next))
    t2 = asyncio.create_task(lock_middleware.dispatch(ctx, call_next))
    t3 = asyncio.create_task(lock_middleware.dispatch(ctx, call_next))

    # Two should start immediately (concurrency_limit=2)
    await asyncio.sleep(0.05)
    assert counter == 2

    # Finish t1 and t2
    await t1
    await t2

    await asyncio.sleep(0.01)  # Give t3 a chance to enter
    # Now t3 should have been able to proceed
    assert counter == 3
    await t3


@pytest.mark.asyncio
async def test_async_lock_cleanup(ctx):
    def key_extractor(c):
        return c.event["data"]

    lock_middleware = AsyncLock(key_extractor=key_extractor, concurrency_limit=1)

    async def call_next(c):
        await asyncio.sleep(0.1)

    key = key_extractor(ctx)

    # Before dispatch
    assert key not in lock_middleware._semaphores

    # Start dispatch
    t1 = asyncio.create_task(lock_middleware.dispatch(ctx, call_next))
    await asyncio.sleep(0.05)

    # Semaphore should exist and ref_count should be 1
    assert key in lock_middleware._semaphores
    assert lock_middleware._semaphores[key].ref_count == 1

    # Start another dispatch for same key
    t2 = asyncio.create_task(lock_middleware.dispatch(ctx, call_next))
    # Wait a bit but not enough for t1 to finish
    await asyncio.sleep(0.01)

    # t2 should be waiting, so ref_count should be 2
    assert lock_middleware._semaphores[key].ref_count == 2

    # Finish t1
    await t1
    # ref_count should be 1
    assert key in lock_middleware._semaphores
    assert lock_middleware._semaphores[key].ref_count == 1

    # Finish t2
    await t2
    # Semaphore should be removed from dict
    assert key not in lock_middleware._semaphores


@pytest.mark.asyncio
async def test_async_lock_exception_handling(ctx):
    def key_extractor(c):
        return c.event["data"]

    lock_middleware = AsyncLock(key_extractor=key_extractor, concurrency_limit=1)

    async def call_next(c):
        raise Exception("error")

    key = key_extractor(ctx)

    with pytest.raises(Exception, match="error"):
        await lock_middleware.dispatch(ctx, call_next)

    # Check that cleanup happened even on exception
    assert key not in lock_middleware._semaphores


@pytest.mark.asyncio
async def test_async_lock_stress():
    def key_extractor(c):
        return c.event["key"]

    lock_middleware = AsyncLock(key_extractor=key_extractor, concurrency_limit=1)

    num_requests = 100
    num_keys = 5

    call_next_counts = {}

    async def call_next(c: EventHandlerContext):
        k = key_extractor(c)
        # Check if another task is already executing for this key
        assert call_next_counts.get(k, 0) == 0
        call_next_counts[k] = call_next_counts.get(k, 0) + 1
        await asyncio.sleep(0.001)
        call_next_counts[k] -= 1
        return k

    tasks = []
    for i in range(num_requests):
        ctx = EventHandlerContext(event={"key": f"key_{i % num_keys}"}, subscription_pattern=(), actual_event_route=())
        tasks.append(asyncio.create_task(lock_middleware.dispatch(ctx, call_next)))

    results = await asyncio.gather(*tasks)

    assert len(results) == num_requests
    assert len(lock_middleware._semaphores) == 0
