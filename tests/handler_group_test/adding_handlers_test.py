import pytest

from dispytch.listener.handler_group import HandlerGroup


def test_register_handler_with_explicit_topic_and_event():
    hg = HandlerGroup()

    @hg.handler(topic="topic1", event="event1")
    def handler_fn():
        return "handled"

    handlers = hg.handlers["topic1"]["event1"]
    assert len(handlers) == 1
    assert handlers[0].func == handler_fn


def test_register_handler_uses_default_topic_and_event():
    hg = HandlerGroup(default_topic="def_topic", default_event="def_event")

    @hg.handler()
    def handler_fn():
        return "handled"

    handlers = hg.handlers["def_topic"]["def_event"]
    assert len(handlers) == 1
    assert handlers[0].func == handler_fn


def test_missing_topic_raises_type_error():
    hg = HandlerGroup()
    with pytest.raises(TypeError, match="Topic not specified"):
        @hg.handler(event="event1")
        def handler_fn():
            pass


def test_missing_event_raises_type_error():
    hg = HandlerGroup()
    with pytest.raises(TypeError, match="Event not specified"):
        @hg.handler(topic="topic1")
        def handler_fn():
            pass


def test_handler_retries_parameters_set_correctly():
    hg = HandlerGroup(default_topic="t", default_event="e")

    @hg.handler(retries=3, retry_on=ValueError, retry_interval=0.5)
    def handler_fn():
        pass

    h = hg.handlers["t"]["e"][0]
    assert h.retries == 3
    assert h.retry_on == ValueError
    assert h.retry_interval == 0.5


def test_register_multiple_handlers_on_same_topic_event():
    hg = HandlerGroup(default_topic="t", default_event="e")

    @hg.handler()
    def h1():
        pass

    @hg.handler()
    def h2():
        pass

    handlers = hg.handlers["t"]["e"]
    assert len(handlers) == 2
    assert handlers[0].func == h1
    assert handlers[1].func == h2


def test_explicit_topic_overwrites_default():
    hg = HandlerGroup(default_topic="default_topic", default_event="default_event")

    @hg.handler(topic="explicit_topic")
    def handler_fn():
        pass

    assert "explicit_topic" in hg.handlers
    assert "default_topic" not in hg.handlers
    assert handler_fn == hg.handlers["explicit_topic"]["default_event"][0].func


def test_explicit_event_overwrites_default():
    hg = HandlerGroup(default_topic="default_topic", default_event="default_event")

    @hg.handler(event="explicit_event")
    def handler_fn():
        pass

    assert "explicit_event" in hg.handlers["default_topic"]
    assert "default_event" not in hg.handlers["default_topic"]
    assert handler_fn == hg.handlers["default_topic"]["explicit_event"][0].func
