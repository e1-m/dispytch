import pytest

from dispytch.dispatcher.trie import Trie


def handler(name):
    return lambda: name


@pytest.fixture
def tree():
    return Trie()


def test_mismatch_wrong_static_segment(tree):
    h = handler("G")
    tree.insert("alpha:beta".split(':'), h)
    assert tree.get("alpha:gamma".split(':')) == []


def test_mismatch_partial_topic(tree):
    h = handler("F")
    tree.insert("a:b:c".split(':'), h)
    assert tree.get("a:b".split(':')) == []


def test_mismatch_with_dynamic_center(tree):
    h = handler("F")
    tree.insert("a:{smth}:c".split(':'), h)
    assert tree.get("a:b:d".split(':')) == []


def test_no_handler(tree):
    assert tree.get("ghost:topic".split(':')) == []
