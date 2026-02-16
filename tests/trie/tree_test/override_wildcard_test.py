import pytest
from dispytch.dispatcher.trie import Trie


def handler(name):
    return lambda: name


@pytest.fixture
def tree():
    return Trie()


def test_override_wildcard_true_exact_match_found(tree):
    h_exact = handler("exact")
    h_wildcard = handler("wildcard")

    tree.insert(("foo", "42"), h_exact)
    tree.insert(("foo", "{id}"), h_wildcard)

    # When override_wildcard=True and exact match exists, wildcard should be ignored
    result = tree.get(("foo", "42"), override_wildcard=True)
    assert result == [h_exact]


def test_override_wildcard_true_no_exact_match(tree):
    h_wildcard = handler("wildcard")

    tree.insert(("foo", "{id}"), h_wildcard)

    # When override_wildcard=True and NO exact match exists, wildcard should be returned
    result = tree.get(("foo", "bar"), override_wildcard=True)
    assert result == [h_wildcard]


def test_override_wildcard_false_returns_both(tree):
    h_exact = handler("exact")
    h_wildcard = handler("wildcard")

    tree.insert(("foo", "42"), h_exact)
    tree.insert(("foo", "{id}"), h_wildcard)

    # Default behavior (override_wildcard=False) should return both
    result = tree.get(("foo", "42"), override_wildcard=False)
    assert set(result) == {h_exact, h_wildcard}


def test_override_wildcard_nested_segments(tree):
    h1 = handler("h1")  # foo:bar:baz
    h2 = handler("h2")  # foo:*:baz
    h3 = handler("h3")  # *:bar:baz
    h4 = handler("h4")  # *:*:baz

    tree.insert(("foo", "bar", "baz"), h1)
    tree.insert(("foo", "*", "baz"), h2)
    tree.insert(("*", "bar", "baz"), h3)
    tree.insert(("*", "*", "baz"), h4)

    # override_wildcard=True
    # For "foo", "bar", "baz":
    # segment 0: "foo" is in children -> values from children["foo"].get(["bar", "baz"], True)
    # segment 0: "foo" is in children -> if override_wildcard=True, we DON'T check "*"
    # children["foo"].get(["bar", "baz"], True):
    #   segment 1: "bar" is in children -> values from children["bar"].get(["baz"], True)
    #   segment 1: "bar" is in children -> if override_wildcard=True, we DON'T check "*"
    # children["bar"].get(["baz"], True):
    #   segment 2: "baz" is in children -> values from children["baz"].get([], True) -> [h1]

    result = tree.get(("foo", "bar", "baz"), override_wildcard=True)
    assert result == [h1]


def test_override_wildcard_partial_exact_match(tree):
    h_wildcard_root = handler("wildcard_root")  # *:bar
    h_exact_bar = handler("exact_bar")  # foo:bar

    tree.insert(("*", "bar"), h_wildcard_root)
    tree.insert(("foo", "bar"), h_exact_bar)

    # Searching for ("foo", "bar")
    # segment 0: "foo" matches exactly. Since override_wildcard=True, "*" is skipped.
    # Result should be [h_exact_bar]
    assert tree.get(("foo", "bar"), override_wildcard=True) == [h_exact_bar]

    # Searching for ("other", "bar")
    # segment 0: "other" NOT in children. Check "*".
    # Result should be [h_wildcard_root]
    assert tree.get(("other", "bar"), override_wildcard=True) == [h_wildcard_root]
