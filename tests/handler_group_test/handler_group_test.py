import pytest
from unittest.mock import Mock
from dispytch.listener.handler_group import HandlerGroup
from dispytch.listener.consumer import EventSubscription
from dispytch.listener.dlq import DeadLetterHandler
from dispytch.listener.retry_policy import RetryPolicy


class MockSubscription(EventSubscription):
    topic: str
    event: str


@pytest.fixture
def mock_dlh():
    return Mock(spec=DeadLetterHandler)


@pytest.fixture
def mock_retry_policy():
    return Mock(spec=RetryPolicy)


def test_handler_group_initialization():
    hg = HandlerGroup()
    assert hg.default_dlh is None
    assert hg.default_retry_policy is None
    assert hg.get_subscriptions() == []


def test_handler_group_initialization_with_defaults(mock_dlh, mock_retry_policy):
    hg = HandlerGroup(default_dlh=mock_dlh, default_retry_policy=mock_retry_policy)
    assert hg.default_dlh == mock_dlh
    assert hg.default_retry_policy == mock_retry_policy


def test_register_handler_uses_group_defaults(mock_dlh, mock_retry_policy):
    hg = HandlerGroup(default_dlh=mock_dlh, default_retry_policy=mock_retry_policy)
    sub = MockSubscription(topic="t1", event="e1")

    @hg.handler(sub)
    def my_handler():
        pass

    handlers = hg.get_handlers(sub)
    assert len(handlers) == 1
    assert handlers[0].func == my_handler
    assert handlers[0].dlh == mock_dlh
    assert handlers[0].retry_policy == mock_retry_policy


def test_register_handler_overrides_group_defaults(mock_dlh, mock_retry_policy):
    hg = HandlerGroup(default_dlh=mock_dlh, default_retry_policy=mock_retry_policy)
    sub = MockSubscription(topic="t1", event="e1")
    
    custom_dlh = Mock(spec=DeadLetterHandler)
    custom_retry = Mock(spec=RetryPolicy)

    @hg.handler(sub, dlh=custom_dlh, retry_policy=custom_retry)
    def my_handler():
        pass

    handlers = hg.get_handlers(sub)
    assert len(handlers) == 1
    assert handlers[0].dlh == custom_dlh
    assert handlers[0].retry_policy == custom_retry
    assert handlers[0].dlh != mock_dlh
    assert handlers[0].retry_policy != mock_retry_policy


def test_get_handlers_returns_empty_list_for_unknown_subscription():
    hg = HandlerGroup()
    sub = MockSubscription(topic="unknown", event="unknown")
    assert hg.get_handlers(sub) == []


def test_multiple_handlers_for_same_subscription():
    hg = HandlerGroup()
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
    hg = HandlerGroup()
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
    hg = HandlerGroup()
    sub = MockSubscription(topic="t1", event="e1")

    def my_handler(x):
        return x + 1

    decorated = hg.handler(sub)(my_handler)
    
    assert decorated == my_handler
    assert decorated(5) == 6
