import pytest

from dispytch.listener.handler_tree import HandlerTree


def handler(name):
    return lambda: name


@pytest.fixture
def tree():
    return HandlerTree(delimiter='.')


def test_deep_path_with_mixed_wildcards(tree):
    h1 = handler("H1")
    h2 = handler("H2")
    h3 = handler("H3")
    tree.insert("foo.{x}.bar.{y}", "created", h1)
    tree.insert("foo.123.bar.{y}", "created", h2)
    tree.insert("foo.{x}.bar.456", "created", h3)

    matched = tree.get("foo.123.bar.456", "created")

    assert set(matched) == {h1, h2, h3}


def test_multiple_branches(tree):
    h1 = handler("J1")
    h2 = handler("J2")
    tree.insert("alpha.{x}", "read", h1)
    tree.insert("alpha.beta", "read", h2)

    assert set(tree.get("alpha.beta", "read")) == {h1, h2}
    assert tree.get("alpha.123", "read") == [h1]
    assert tree.get("alpha.xyz", "read") == [h1]
