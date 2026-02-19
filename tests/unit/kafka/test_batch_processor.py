import asyncio
import pytest
from unittest.mock import AsyncMock
from dispytch.kafka.batch_processor import BatchProcessor


@pytest.mark.asyncio
async def test_batch_by_size():
    handler = AsyncMock()
    processor = BatchProcessor(handler, batch_timeout_ms=1000, batch_size=3)

    await processor.add("v1")
    await processor.add("v2")
    handler.assert_not_called()

    await processor.add("v3")
    handler.assert_called_once_with(["v1", "v2", "v3"])


@pytest.mark.asyncio
async def test_batch_by_timeout():
    handler = AsyncMock()
    # 100ms timeout
    processor = BatchProcessor(handler, batch_timeout_ms=100, batch_size=10)

    await processor.add("v1")
    handler.assert_not_called()

    # Wait for timeout (100ms * 1.5 to be safe)
    await asyncio.sleep(0.15)
    handler.assert_called_once_with(["v1"])


@pytest.mark.asyncio
async def test_timer_cancellation_on_size_batch():
    handler = AsyncMock()
    processor = BatchProcessor(handler, batch_timeout_ms=100, batch_size=2)

    await processor.add("v1")
    # Timer started
    assert processor._timer_task is not None
    timer_task = processor._timer_task

    await processor.add("v2")
    # Batch committed by size
    handler.assert_called_once_with(["v1", "v2"])

    # Wait a bit for the event loop to process the cancellation and the next steps in add()
    await asyncio.sleep(0)

    # Timer should be cancelled or replaced if add() continued
    assert timer_task.cancelling() > 0 or timer_task.cancelled()

    # Doesn't start a new timer.
    assert processor._timer_task is None


@pytest.mark.asyncio
async def test_multiple_batches():
    handler = AsyncMock()
    processor = BatchProcessor(handler, batch_timeout_ms=1000, batch_size=2)

    await processor.add("v1")
    await processor.add("v2")
    handler.assert_called_once_with(["v1", "v2"])
    handler.reset_mock()

    await processor.add("v3")
    await processor.add("v4")
    handler.assert_called_once_with(["v3", "v4"])


@pytest.mark.asyncio
async def test_duplicate_items_in_batch():
    handler = AsyncMock()
    processor = BatchProcessor(handler, batch_timeout_ms=1000, batch_size=2)

    await processor.add("v1")
    await processor.add("v1")

    handler.assert_called_once_with(["v1", "v1"])


@pytest.mark.asyncio
async def test_empty_batch_timer_commit():
    handler = AsyncMock()
    processor = BatchProcessor(handler, batch_timeout_ms=100, batch_size=10)

    await processor._commit_batch(reason="time")
    handler.assert_not_called()
    assert processor._timer_task is None
