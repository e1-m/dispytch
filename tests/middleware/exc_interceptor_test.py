from unittest.mock import AsyncMock
import pytest
from dispytch.dispatcher.handler import EventHandlerContext
from dispytch.middleware.exc_interceptor import ExceptionInterceptor


@pytest.fixture
def ctx():
    return EventHandlerContext(
        event={"test": "data"},
        subscription_pattern=("test",),
        actual_event_route=("test",)
    )


@pytest.mark.asyncio
async def test_dispatch_success(ctx):
    middleware = ExceptionInterceptor(handlers={})
    call_next = AsyncMock(return_value="success")

    result = await middleware.dispatch(ctx, call_next)

    assert result == "success"
    call_next.assert_called_once_with(ctx)


@pytest.mark.asyncio
async def test_dispatch_catches_exception(ctx):
    handler = AsyncMock(return_value="handled")
    middleware = ExceptionInterceptor(handlers={ValueError: handler})

    err = ValueError("test error")

    async def call_next(_):
        raise err

    result = await middleware.dispatch(ctx, call_next)

    assert result == "handled"
    handler.assert_called_once_with(ctx, err)


@pytest.mark.asyncio
async def test_dispatch_catches_inheritance(ctx):
    class MyError(ValueError):
        pass

    handler = AsyncMock(return_value="handled subclass")
    middleware = ExceptionInterceptor(handlers={ValueError: handler})

    err = MyError("test subclass error")

    async def call_next(_):
        raise err

    result = await middleware.dispatch(ctx, call_next)

    assert result == "handled subclass"
    handler.assert_called_once_with(ctx, err)


@pytest.mark.asyncio
async def test_dispatch_raises_unhandled(ctx):
    middleware = ExceptionInterceptor(handlers={ValueError: AsyncMock()})

    err = TypeError("unhandled error")

    async def call_next(_):
        raise err

    with pytest.raises(TypeError) as excinfo:
        await middleware.dispatch(ctx, call_next)

    assert excinfo.value is err


@pytest.mark.asyncio
async def test_add_handler(ctx):
    middleware = ExceptionInterceptor(handlers={})
    handler = AsyncMock(return_value="added handler")

    middleware.add_handler(KeyError, handler)

    err = KeyError("test key error")

    async def call_next(_):
        raise err

    result = await middleware.dispatch(ctx, call_next)

    assert result == "added handler"
    handler.assert_called_once_with(ctx, err)


@pytest.mark.asyncio
async def test_dispatch_precedence(ctx):
    class ParentError(Exception):
        pass

    class ChildError(ParentError):
        pass

    parent_handler = AsyncMock(return_value="parent")
    child_handler = AsyncMock(return_value="child")

    middleware = ExceptionInterceptor(handlers={
        ParentError: parent_handler,
        ChildError: child_handler
    })

    err = ChildError("test precedence")

    async def call_next(_):
        raise err

    result = await middleware.dispatch(ctx, call_next)

    assert result == "child"
    child_handler.assert_called_once_with(ctx, err)
    parent_handler.assert_not_called()
