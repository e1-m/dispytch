import asyncio
from unittest.mock import Mock, AsyncMock, call, patch
import pytest
from dispytch.listener.handler import EventHandlerContext
from dispytch.middleware.retry import Retry


@pytest.fixture
def ctx():
    return EventHandlerContext(
        event={"test": "data"},
        subscription_pattern=("test",),
        actual_event_route=("test",)
    )


@pytest.mark.asyncio
async def test_retry_middleware_success_on_first_try(ctx):
    mock_policy = Mock()
    middleware = Retry(retry_policy=mock_policy)

    call_next = AsyncMock(return_value="success")

    result = await middleware.dispatch(ctx, call_next)

    assert result == "success"
    call_next.assert_called_once_with(ctx)
    mock_policy.should_retry.assert_not_called()


@pytest.mark.asyncio
async def test_retry_middleware_retries_and_succeeds(ctx):
    mock_policy = Mock()
    mock_policy.should_retry.side_effect = [True, True, False]
    mock_policy.get_delay.return_value = 0

    err1 = ValueError("fail1")
    err2 = ValueError("fail2")
    call_next = AsyncMock(side_effect=[err1, err2, "success"])

    middleware = Retry(retry_policy=mock_policy)

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        result = await middleware.dispatch(ctx, call_next)

    assert result == "success"
    assert call_next.call_count == 3

    mock_policy.should_retry.assert_has_calls([
        call(0, err1),
        call(1, err2)
    ])

    assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_retry_middleware_raises_after_max_retries(ctx):
    mock_policy = Mock()
    mock_policy.should_retry.side_effect = [True, True, False]
    mock_policy.get_delay.return_value = 0

    err1 = ValueError("fail1")
    err2 = ValueError("fail2")
    err3 = ValueError("fail3")
    call_next = AsyncMock(side_effect=[err1, err2, err3])

    middleware = Retry(retry_policy=mock_policy)

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        with pytest.raises(ValueError) as exc_info:
            await middleware.dispatch(ctx, call_next)

    assert exc_info.value == err3
    assert call_next.call_count == 3

    mock_policy.should_retry.assert_has_calls([
        call(0, err1),
        call(1, err2),
        call(2, err3)
    ])


@pytest.mark.asyncio
async def test_retry_middleware_passes_prev_delay_correctly(ctx):
    mock_policy = Mock()
    mock_policy.should_retry.side_effect = [True, True, False]
    mock_policy.get_delay.side_effect = [1.0, 2.0]

    call_next = AsyncMock(side_effect=[ValueError, ValueError, ValueError])
    middleware = Retry(retry_policy=mock_policy)

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        with pytest.raises(ValueError):
            await middleware.dispatch(ctx, call_next)

    mock_policy.get_delay.assert_has_calls([
        call(0, 0.0),
        call(1, 1.0)
    ])

    mock_sleep.assert_has_calls([
        call(1.0),
        call(2.0)
    ])
