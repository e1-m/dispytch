import pytest

from dispytch.listener.handler_group import HandlerGroup
from dispytch.listener.consumer import EventSubscription


class BrokerNeutralTestSubscription(EventSubscription):
    topic: str = "*"
    event: str = "*"


def test_register_handler_with_explicit_topic_and_event():
    hg = HandlerGroup()

    @hg.handler(BrokerNeutralTestSubscription(topic="topic1", event="event1"))
    def handler_fn():
        return "handled"

    handlers = hg.get_handlers(BrokerNeutralTestSubscription(topic="topic1", event="event1"))
    assert len(handlers) == 1
    assert handlers[0].func == handler_fn


def test_handler_retries_parameters_set_correctly():
    hg = HandlerGroup()

    @hg.handler(BrokerNeutralTestSubscription(topic="t", event="e"),
                retries=3, retry_on=(ValueError,), max_delay_sec=15.0)
    def handler_fn():
        pass

    h = hg.get_handlers(BrokerNeutralTestSubscription(topic="t", event="e"))[0]
    assert h.retries == 3
    assert h.retry_on == (ValueError,)
    assert h.max_delay == 15.0


def test_register_multiple_handlers_on_same_topic_event():
    hg = HandlerGroup()

    @hg.handler(BrokerNeutralTestSubscription(topic="t", event="e"))
    def h1():
        pass

    @hg.handler(BrokerNeutralTestSubscription(topic="t", event="e"))
    def h2():
        pass

    handlers = hg.get_handlers(BrokerNeutralTestSubscription(topic="t", event="e"))
    assert len(handlers) == 2
    assert handlers[0].func == h1
    assert handlers[1].func == h2
