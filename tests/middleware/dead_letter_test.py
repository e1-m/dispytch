from unittest.mock import Mock, AsyncMock
import pytest
from dispytch.listener.handler import EventHandlerContext
from dispytch.middleware.dead_letter import DeadLetter, DeadLetterHandler


@pytest.fixture
def ctx():
    return EventHandlerContext(
        event={"test": "data"},
        subscription_pattern=("test",),
        actual_event_route=("test",)
    )


@pytest.mark.asyncio
async def test_dead_letter_middleware_success(ctx):
    mock_dlh = AsyncMock()
    middleware = DeadLetter(dlh=mock_dlh)

    call_next = AsyncMock(return_value="success")

    result = await middleware.dispatch(ctx, call_next)

    assert result == "success"
    call_next.assert_called_once_with(ctx)
    mock_dlh.handle.assert_not_called()


@pytest.mark.asyncio
async def test_dead_letter_middleware_calls_dlh_on_failure(ctx):
    mock_dlh = AsyncMock()
    middleware = DeadLetter(dlh=mock_dlh)

    err = ValueError("failure")
    call_next = AsyncMock(side_effect=err)

    await middleware.dispatch(ctx, call_next)

    call_next.assert_called_once_with(ctx)
    mock_dlh.handle.assert_called_once_with(ctx, err)


@pytest.mark.asyncio
async def test_dead_letter_middleware_does_not_swallow_dlh_errors(ctx):
    mock_dlh = AsyncMock()
    mock_dlh.handle.side_effect = RuntimeError("dlh failed")
    middleware = DeadLetter(dlh=mock_dlh)

    call_next = AsyncMock(side_effect=ValueError("original failure"))

    with pytest.raises(RuntimeError) as exc_info:
        await middleware.dispatch(ctx, call_next)

    assert str(exc_info.value) == "dlh failed"
