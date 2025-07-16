import pytest

from dispytch.listener.handler_tree import HandlerTree


def handler(name):
    return lambda: name


@pytest.fixture
def tree():
    return HandlerTree(delimiter=':')


def test_mismatch_different_event(tree):
    h = handler("E")
    tree.insert("a:b", "create", h)
    assert tree.get("a:b", "delete") == []


def test_mismatch_wrong_static_segment(tree):
    h = handler("G")
    tree.insert("alpha:beta", "done", h)
    assert tree.get("alpha:gamma", "done") == []


def test_mismatch_partial_topic(tree):
    h = handler("F")
    tree.insert("a:b:c", "event", h)
    assert tree.get("a:b", "event") == []


def test_mismatch_with_dynamic_center(tree):
    h = handler("F")
    tree.insert("a:{smth}:c", "event", h)
    assert tree.get("a:b:d", "event") == []


def test_no_handler(tree):
    assert tree.get("ghost:topic", "event") == []
