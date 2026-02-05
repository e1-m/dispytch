from typing import Any
from unittest.mock import Mock, AsyncMock, call, patch

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
async def test_handler_works_without_retry_policy_and_dlh_on_success(di_mock):
    mock_func = Mock(return_value="success")
    handler = Handler(func=mock_func, retry_policy=None, dlh=None)

    result = await handler.handle(di_mock({"some": "deps"}))

    mock_func.assert_called_once()

    assert result == "success"


@pytest.mark.asyncio
async def test_handler_raises_error_without_retry_policy_on_failure(di_mock):
    mock_func = Mock(side_effect=ValueError)
    handler = Handler(func=mock_func, retry_policy=None, dlh=None)

    with pytest.raises(ValueError):
        await handler.handle(di_mock({"some": "deps"}))


@pytest.mark.asyncio
async def test_handler_follows_retry_policy_and_raises_error_on_failure(di_mock):
    mock_policy = Mock()
    mock_policy.should_retry.side_effect = [True, True, False]
    mock_policy.get_delay.return_value = 0

    mock_func = Mock(side_effect=[ValueError, ValueError, ValueError, "success"])
    handler = Handler(func=mock_func, retry_policy=mock_policy, dlh=None)

    with pytest.raises(ValueError):
        await handler.handle(di_mock({"some": "deps"}))

    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_handler_follows_retry_policy_and_does_not_raise_error_on_success(di_mock):
    mock_policy = Mock()
    mock_policy.should_retry.side_effect = [True, True, False]
    mock_policy.get_delay.return_value = 0

    mock_func = Mock(side_effect=[ValueError, ValueError, "success"])
    handler = Handler(func=mock_func, retry_policy=mock_policy, dlh=None)

    result = await handler.handle(di_mock({"some": "deps"}))

    assert mock_func.call_count == 3
    assert result == "success"


@pytest.mark.asyncio
async def test_handler_correctly_passes_args_to_retry_policy(di_mock):
    mock_policy = Mock()
    mock_policy.should_retry.side_effect = [True, True, False]
    mock_policy.get_delay.side_effect = [1.1, 2.2, 3.3]

    err1 = ValueError("First failure")
    err2 = TypeError("Second failure")

    mock_func = Mock(side_effect=[err1, err2, "success"])
    handler = Handler(func=mock_func, retry_policy=mock_policy, dlh=None)

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        result = await handler.handle(di_mock({"some": "deps"}))

    mock_policy.should_retry.assert_has_calls([
        call(0, err1),
        call(1, err2),
    ])

    mock_policy.get_delay.assert_has_calls([
        call(0, 0.0),
        call(1, 1.1),
    ])

    mock_sleep.assert_has_calls([
        call(1.1),
        call(2.2)
    ])

    assert result == "success"
