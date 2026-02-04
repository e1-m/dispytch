from typing import Any
from unittest.mock import Mock, AsyncMock

import pytest
import pytest_asyncio

from dispytch.listener.handler import Handler


@pytest_asyncio.fixture
def di_mock():
    def inner(deps: dict[str, Any]):
        cm_mock = AsyncMock()
        cm_mock.__aenter__.return_value = deps
        cm_mock.__aexit__.return_value = None

        di = Mock()
        di.resolve.return_value = cm_mock
        return di

    return inner


@pytest.mark.asyncio
async def test_handler_raises_error_when_dhl_is_none_on_failure(di_mock):
    mock_func = Mock(side_effect=ValueError)
    handler = Handler(func=mock_func, retry_policy=None, dlh=None)

    with pytest.raises(ValueError):
        await handler.handle(di_mock({"some": "deps"}))


@pytest.mark.asyncio
async def test_handler_dlh_is_not_called_on_success(di_mock):
    mock_func = Mock(return_value="success")
    mock_dlh = AsyncMock()
    handler = Handler(func=mock_func, retry_policy=None, dlh=mock_dlh)

    await handler.handle(di_mock({"some": "deps"}))
    mock_func.assert_called_once()
    mock_dlh.handle.assert_not_called()


@pytest.mark.asyncio
async def test_handler_dlh_is_called_on_failure(di_mock):
    mock_func = Mock(side_effect=ValueError)
    mock_dlh = AsyncMock()
    handler = Handler(func=mock_func, retry_policy=None, dlh=mock_dlh)

    await handler.handle(di_mock({"some": "deps"}))
    mock_func.assert_called_once()
    mock_dlh.handle.assert_called_once()


@pytest.mark.asyncio
async def test_handler_dlh_is_called_when_retries_exhausted_on_failure(di_mock):
    mock_func = Mock(side_effect=[ValueError, ValueError])
    mock_dlh = AsyncMock()
    retry_policy = Mock()
    retry_policy.should_retry.side_effect = [True, False]
    retry_policy.get_delay.return_value = 0
    handler = Handler(func=mock_func, retry_policy=retry_policy, dlh=mock_dlh)

    await handler.handle(di_mock({"some": "deps"}))

    assert mock_func.call_count == 2
    mock_dlh.handle.assert_called_once()


@pytest.mark.asyncio
async def test_handler_dlh_is_not_called_when_retries_exhausted_on_success(di_mock):
    mock_func = Mock(side_effect=[ValueError, ValueError, "success"])
    mock_dlh = AsyncMock()
    retry_policy = Mock()
    retry_policy.should_retry.side_effect = [True, True, False]
    retry_policy.get_delay.return_value = 0
    handler = Handler(func=mock_func, retry_policy=retry_policy, dlh=mock_dlh)

    result = await handler.handle(di_mock({"some": "deps"}))

    assert mock_func.call_count == 3
    assert result == "success"
    mock_dlh.handle.assert_not_called()
