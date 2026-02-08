from unittest.mock import Mock, AsyncMock
import pytest
from dispytch.listener.handler import EventHandlerContext
from dispytch.middleware.filter import FilterMiddleware


@pytest.fixture
def ctx():
    return EventHandlerContext(
        event={"test": "data"},
        subscription_pattern=("test",),
        actual_event_route=("test",)
    )


@pytest.mark.asyncio
async def test_filter_middleware_allows_event(ctx):
    filter_func = Mock(return_value=True)
    middleware = FilterMiddleware(filter=filter_func)
    call_next = AsyncMock(return_value="success")

    result = await middleware.dispatch(ctx, call_next)

    assert result == "success"
    filter_func.assert_called_once_with(ctx)
    call_next.assert_called_once_with(ctx)


@pytest.mark.asyncio
async def test_filter_middleware_blocks_event(ctx):
    filter_func = Mock(return_value=False)
    middleware = FilterMiddleware(filter=filter_func)
    call_next = AsyncMock()

    result = await middleware.dispatch(ctx, call_next)

    assert result is None
    filter_func.assert_called_once_with(ctx)
    call_next.assert_not_called()
