import pytest

from dispytch.listener.handler_tree import HandlerTree


def handler(name):
    return lambda: name


@pytest.fixture
def tree():
    return HandlerTree(delimiter=':')


def test_exact_match(tree):
    h = handler("A")
    tree.insert("foo:bar", "created", h)
    assert tree.get("foo:bar", "created") == [h]


def test_wildcard_match(tree):
    h = handler("A")
    tree.insert("foo:*", "created", h)
    assert tree.get("foo:bar", "created") == [h]


def test_get_by_wildcard(tree):
    h = handler("A")
    tree.insert("foo:*", "created", h)
    assert tree.get("foo:*", "created") == [h]


def test_dynamic_segment_match(tree):
    h = handler("B")
    tree.insert("foo:{id}", "deleted", h)
    assert tree.get("foo:123", "deleted") == [h]
    assert tree.get("foo:xyz", "deleted") == [h]


def test_multiple_handlers_same_key(tree):
    h1 = handler("C1")
    h2 = handler("C2")
    tree.insert("x:y", "updated", h1, h2)
    assert tree.get("x:y", "updated") == [h1, h2]


def test_wildcard_and_exact_coexist(tree):
    h1 = handler("D1")
    h2 = handler("D2")
    tree.insert("foo:{id}", "read", h1)
    tree.insert("foo:42", "read", h2)

    assert set(tree.get("foo:42", "read")) == {h1, h2}
