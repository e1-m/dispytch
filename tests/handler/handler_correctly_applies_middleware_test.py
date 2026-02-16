import pytest
from typing import Any
from dispytch.dispatcher.handler import Handler, EventHandlerContext, NextCall, Middleware
from dispytch.di.event import Event


@pytest.fixture
def ctx():
    return EventHandlerContext(
        event={"key": "value"},
        subscription_pattern=("test",),
        actual_event_route=("test",)
    )


class AppendMiddleware:
    def __init__(self, value: str):
        self.value = value

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall) -> Any:
        if "order" not in ctx.event:
            ctx.event["order"] = []

        ctx.event["order"].append(f"{self.value}")
        return await call_next(ctx)


class EarlyReturnMiddleware:
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall) -> Any:
        return None


@pytest.mark.asyncio
async def test_handler_works_without_middlewares(ctx):
    async def target_func(event: Event):
        assert event.get("key", None) == "value"

    handler = Handler(func=target_func, middlewares=None)

    await handler.handle(ctx)


@pytest.mark.asyncio
async def test_handler_applies_single_middleware(ctx):
    async def target_func(event: Event):
        assert event["order"] == ["m1"]

    middleware = AppendMiddleware("m1")
    handler = Handler(func=target_func, middlewares=[middleware])

    await handler.handle(ctx)


@pytest.mark.asyncio
async def test_handler_applies_multiple_middlewares_in_correct_order(ctx):
    async def target_func():
        assert ctx.event["order"] == [
            "m1", "m2", "m3",
        ]

    m1 = AppendMiddleware("m1")
    m2 = AppendMiddleware("m2")
    m3 = AppendMiddleware("m3")

    handler = Handler(func=target_func, middlewares=[m1, m2, m3])

    await handler.handle(ctx)


@pytest.mark.asyncio
async def test_middleware_can_return_early(ctx):
    executed = False

    async def target_func():
        nonlocal executed
        executed = True
        return "base"

    handler = Handler(func=target_func, middlewares=[EarlyReturnMiddleware()])

    await handler.handle(ctx)

    assert not executed
