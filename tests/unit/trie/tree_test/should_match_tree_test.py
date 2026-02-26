import pytest

from dispytch.dispatcher.trie import Trie


def handler(name):
    return lambda: name


@pytest.fixture
def tree():
    return Trie()


def test_exact_match(tree):
    h = handler("A")
    tree.insert("foo:bar".split(':'), h)
    assert tree.get("foo:bar".split(':')) == [h]


def test_wildcard_match(tree):
    h = handler("A")
    tree.insert("foo:*".split(':'), h)
    assert tree.get("foo:bar".split(':')) == [h]


def test_get_by_wildcard(tree):
    h = handler("A")
    tree.insert("foo:*".split(':'), h)
    assert tree.get("foo:*".split(':')) == [h]


def test_dynamic_segment_match(tree):
    h = handler("B")
    tree.insert("foo:{id}".split(':'), h)
    assert tree.get("foo:123".split(':')) == [h]
    assert tree.get("foo:xyz".split(':')) == [h]


def test_multiple_handlers_same_key(tree):
    h1 = handler("C1")
    h2 = handler("C2")
    tree.insert("x:y".split(':'), h1)
    tree.insert("x:y".split(':'), h2)
    assert tree.get("x:y".split(':'),) == [h1, h2]


def test_wildcard_and_exact_coexist(tree):
    h1 = handler("D1")
    h2 = handler("D2")
    tree.insert("foo:{id}".split(':'), h1)
    tree.insert("foo:42".split(':'), h2)

    assert set(tree.get("foo:42".split(':'))) == {h1, h2}
