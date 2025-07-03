from unittest.mock import Mock

import pytest

from dispytch.listener.handler import Handler


@pytest.mark.asyncio
async def test_handler_without_retries():
    """Test that handler works correctly without retries."""
    mock_func = Mock(return_value="success")
    handler = Handler(func=mock_func, retries=0)

    result = await handler.handle()

    mock_func.assert_called_once()
    assert result == "success"


@pytest.mark.asyncio
async def test_handler_with_retries_no_exception():
    """Test that handler doesn't retry when no exception is raised."""
    mock_func = Mock(return_value="success")
    handler = Handler(func=mock_func, retries=3)

    result = await handler.handle()

    mock_func.assert_called_once()
    assert result == "success"


@pytest.mark.asyncio
async def test_handler_zero_retries_with_exception():
    """Test that handler doesn't retry when retries=0 and exception occurs."""
    mock_func = Mock(side_effect=ValueError)
    handler = Handler(func=mock_func, retries=0)

    with pytest.raises(ValueError):
        await handler.handle()

    mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_handler_exhausts_retries():
    """Test that handler raises exception when retries are exhausted."""
    mock_func = Mock(side_effect=[ValueError, ValueError, ValueError, ValueError])
    handler = Handler(func=mock_func, retries=3)

    with pytest.raises(ValueError):
        await handler.handle()

    assert mock_func.call_count == 4


@pytest.mark.asyncio
async def test_handler_with_successful_retry_after_multiple_failures():
    """Test success after exactly max retries."""
    mock_func = Mock(side_effect=[ValueError, ValueError, ValueError, "success"])
    handler = Handler(func=mock_func, retries=3)

    result = await handler.handle()

    assert mock_func.call_count == 4
    assert result == "success"


@pytest.mark.asyncio
async def test_handler_with_negative_retries():
    """Test that handler handles negative retry values correctly."""
    mock_func = Mock(side_effect=[ValueError, "success"])
    # Handler should convert negative retries to positive
    handler = Handler(func=mock_func, retries=-2)

    result = await handler.handle()

    assert mock_func.call_count == 2
    assert result == "success"
