from unittest.mock import Mock

import pytest

from dispytch.listener.handler import Handler


@pytest.mark.asyncio
async def test_handler_with_retries_all_exceptions():
    """Test that handler retries on all exceptions when retry_on is None."""
    mock_func = Mock(side_effect=[ValueError, KeyError, "success"])
    handler = Handler(func=mock_func, retries=3)

    result = await handler.handle()

    assert mock_func.call_count == 3
    assert result == "success"


@pytest.mark.asyncio
async def test_handler_with_retries_no_exceptions():
    """Test that handler doesn't retry when retry_on is an empty list."""
    mock_func = Mock(side_effect=[ValueError, "success"])
    handler = Handler(func=mock_func, retries=2, retry_on=[])

    with pytest.raises(ValueError):
        await handler.handle()

    mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_handler_with_specific_retry_exceptions():
    """Test that handler only retries on specified exceptions."""
    mock_func = Mock(side_effect=[ValueError, KeyError, "success"])
    handler = Handler(func=mock_func, retries=3, retry_on=[ValueError])

    with pytest.raises(KeyError):
        await handler.handle()

    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_handler_multiple_retry_exceptions():
    """Test that handler retries on multiple specified exception types."""
    mock_func = Mock(side_effect=[ValueError, KeyError, TypeError, "success"])
    handler = Handler(func=mock_func, retries=5, retry_on=[ValueError, KeyError])

    with pytest.raises(TypeError):
        await handler.handle()

    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_handler_exception_inheritance():
    """Test that handler catches subclasses of specified exceptions."""

    class CustomError(ValueError):
        pass

    mock_func = Mock(side_effect=[CustomError, "success"])
    handler = Handler(func=mock_func, retries=2, retry_on=[ValueError])

    result = await handler.handle()

    assert mock_func.call_count == 2
    assert result == "success"
