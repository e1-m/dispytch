import pytest
from unittest.mock import Mock
from dispytch.dispatcher import Router
from dispytch.dispatcher.consumer import EventSubscription
from dispytch.dispatcher.handler import Middleware, EventHandlerContext, NextCall


class MockSubscription(EventSubscription):
    topic: str
    event: str


class MockMiddleware(Middleware):
    def __init__(self, name: str):
        self.name = name

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        return await call_next(ctx)

    def __repr__(self):
        return f"MockMiddleware(name={self.name})"


@pytest.fixture
def mw1():
    return MockMiddleware("mw1")


@pytest.fixture
def mw2():
    return MockMiddleware("mw2")


def test_register_handler_uses_shared_middlewares(mw1, mw2):
    hg = Router(middlewares=[mw1, mw2])
    sub = MockSubscription(topic="t1", event="e1")

    @hg.handler(sub)
    def my_handler():
        pass

    handlers = hg.get_handlers(sub)
    assert len(handlers) == 1
    assert handlers[0].func == my_handler
    assert handlers[0].middlewares == [mw1, mw2]


def test_register_handler_adds_router_and_handler_specific_middlewares(mw1, mw2):
    hg = Router(middlewares=[mw1])
    sub = MockSubscription(topic="t1", event="e1")

    custom_mw = MockMiddleware("custom")

    @hg.handler(sub, middlewares=[custom_mw])
    def my_handler():
        pass

    handlers = hg.get_handlers(sub)
    assert len(handlers) == 1
    assert handlers[0].middlewares == [mw1, custom_mw]


def test_get_handlers_returns_empty_list_for_unknown_subscription():
    hg = Router()
    sub = MockSubscription(topic="unknown", event="unknown")
    assert hg.get_handlers(sub) == []


def test_multiple_handlers_for_same_subscription():
    hg = Router()
    sub = MockSubscription(topic="t1", event="e1")

    @hg.handler(sub)
    def h1(): pass

    @hg.handler(sub)
    def h2(): pass

    handlers = hg.get_handlers(sub)
    assert len(handlers) == 2
    assert handlers[0].func == h1
    assert handlers[1].func == h2


def test_get_subscriptions_returns_unique_subscriptions():
    hg = Router()
    sub1 = MockSubscription(topic="t1", event="e1")
    sub2 = MockSubscription(topic="t2", event="e2")

    @hg.handler(sub1)
    def h1(): pass

    @hg.handler(sub1)
    def h2(): pass

    @hg.handler(sub2)
    def h3(): pass

    subs = hg.get_subscriptions()
    assert len(subs) == 2
    assert sub1 in subs
    assert sub2 in subs


def test_handler_decorator_returns_original_function():
    hg = Router()
    sub = MockSubscription(topic="t1", event="e1")

    def my_handler(x):
        return x + 1

    decorated = hg.handler(sub)(my_handler)

    assert decorated == my_handler
    assert decorated(5) == 6
